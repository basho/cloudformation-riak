#! /usr/bin/env python

import sys
from boto import ec2
import boto.utils
from subprocess import Popen, PIPE, STDOUT
import time

def runcmd(cmd):
    print "Running: %s" % cmd
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
    output = p.stdout.read()
    output.strip()
    return output

def get_group_info(ec2conn, instance_id) :
    reservations = ec2conn.get_all_instances(instance_id)
    instance = [i for r in reservations for i in r.instances][0]
    if instance.tags.has_key('aws:autoscaling:groupName'):
        private_ip, first_node, nodes_total, stack_id, node_number, instance = get_autoscale_info(ec2conn, instance)
    elif instance.tags.has_key('stackId'):
        private_ip, first_node, nodes_total, stack_id, node_number, instance = get_reservation_info(ec2conn, instance)
    else:
        return None
    return private_ip, first_node, nodes_total, stack_id, node_number, instance

def get_autoscale_info(ec2conn, instance) :
    autoscale_group = instance.tags['aws:autoscaling:groupName']
    private_ip = instance.private_ip_address
    filters = {'tag:aws:autoscaling:groupName': '%s*' % autoscale_group, 'instance-state-name': 'running'}
    reservations = ec2conn.get_all_instances(filters=filters)
    instances = [i for r in reservations for i in r.instances]
    sorted_instances = sorted(instances, key=lambda i: (i.launch_time, i.id))
    first_node = sorted_instances[0]
    node_number = [si.id for si in sorted_instances].index(instance.id) + 1
    return private_ip, first_node, len(sorted_instances), autoscale_group, node_number, instance


def get_reservation_info(ec2conn, instance) :
    found = False
    while found != True:
        try:
            stack_id = instance.tags['stackId']
            nodes_total = int(instance.tags['nodesTotal'])
            node_number = int(instance.tags['nodeNumber'])
            break
        except:
            time.sleep(10)
            print'Waiting for tags'
    private_ip = instance.private_ip_address

    filters = {'tag:stackId': stack_id, 'tag:nodeNumber': '1' }
    reservations = ec2conn.get_all_instances(filters=filters)
    instances = [i for r in reservations for i in r.instances]
    first_node = instances[0]
    return private_ip, first_node, int(nodes_total), stack_id, node_number, instance

def plan_commit(total_nodes):
    ready = False
    committed = False
    planned = False
    #wait until the ring is in a ready phase
    while ready == False:
        output=runcmd('riak-admin ring-status|grep "Ring Ready"')
        if output.find('Ring Ready: true') != -1:
            ready = True
            break
        time.sleep(5)
    #keep planning until total nodes are equal to staged nodes
    while planned == False:
        output=runcmd("riak-admin cluster plan")
        print output
        staged_nodes = output.count("valid")
        print "Total Nodes: %s  Staged Nodes %s" % (str(total_nodes), str(staged_nodes))
        if staged_nodes == total_nodes:
            break
        time.sleep(5)
    #commit changes to the cluster
    while committed == False:
        output=runcmd("riak-admin cluster commit")
        print output
        if output.find('Cluster changes committed') != -1:
            committed = True
            return
        time.sleep(5)

instance_data = boto.utils.get_instance_metadata()
instance_id = instance_data["instance-id"]

# connect to region of the current instance rather than default of us-east-1
zone = instance_data['placement']['availability-zone']
region_name = zone[:-1]

print "Connecting to region %s" % region_name
ec2conn = ec2.connect_to_region(region_name)
private_ip, first_node, nodes_total, stack_id, node_number, instance = get_group_info(ec2conn, instance_id)

print "Instance belongs to %s. Finding first node" % stack_id
print "Node number for this machine is %s." % node_number
print "Node count for this cluster is %s." % nodes_total
print "First node in the cluster is %s" % first_node.private_ip_address
print "Private IP for this machine is %s." % private_ip


output = runcmd ('riak-admin member-status 2> /dev/null | grep ^valid|wc -l')
node_count = int(output)
print "Current node count is %s" % str(node_count)
joined = False

if node_count > 1 :
    print "Node already in cluster."
    joined = True
    sys.exit(0)

if private_ip == first_node.private_ip_address:
    print 'This is the first node in the cluster.  Nodes will join it.'
    sys.exit(0)

#looping through the join until I get a successful request
while joined == False:
    print "Joining node to node: %s." % first_node.private_ip_address
    cmd = ["riak-admin", "cluster",  "join", "riak@%s" % first_node.private_ip_address]
    output = runcmd(" ".join(cmd))
    print output
    if output.find('Success: staged join request') != -1:
        joined = True
        break
    time.sleep(3)

if  node_number == nodes_total:
    print 'This is the last node to join the cluster.  Stage and plan.'
    plan_commit(nodes_total)
