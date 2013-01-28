# Riak AWS CloudFormation Recipes


These [Amazon CloudFormation](http://aws.amazon.com/cloudformation/) recipes are designed to help you get started quickly with a Riak cluster. They are not for production use. All of these recipes build clusters based on Amazon Linux and should work in any AWS region.

The recipes come in 3 flavors: riak cluster, riak vpc cluster, and riak vpc cluster with frontend appservers.

## riak cluster


This builds a a simple riak cluster.  The end result is a fully joined riak cluster.  You have the oppurtunity to pass the following options to the cluster at launch time:

* **RiakClusterSize**
	* The number of nodes that you would like in the cluster	
* **RiakInstanceType**
	* The instance size you'd like to use 	
* **RingSize**
	* The Riak Ring size you want to use  (64,128,256)
* **DiskType**
	* The type of disk you want on your root volume (ebs or ephemeral)	
* **KeyName**
	* The ec2 ssh keypair that you want associated with these instances.  You will use this to log into your instance.  This key must be uploaded prior to launching the cluster.

Once the stack is completed, use your EC2 console to find an IP address of to ssh to and test drive the cluster.

The filename for this recipe is **riak-cluster.json** .
 
This stack can take around 10 minutes to build.  It will build the number of instances specified in RiakClusterSize.

## riak vpc cluster

This recipe builds a Riak cluster inside of a EC2 Virtual Private Cloud (VPC).  This means that the cluster is shut off from the outside.  To access the cluster, you will first need to ssh into the BastionHost.  This recipe has all the same options as riak-cluster plus the following:



* **BastionInstanceType**
	* The ec2 instance type of the bastion host

* **NATInstanceType**
	* The ec2 instance type of the NAT device
	
* **SSHFrom**
	* The IP range which you'd like to allow to SSH to the BastionHost.  Must be a valid CIDR range of the form x.x.x.x/x.
	

Once the stack is completed, check the outputs of the stack to find the BastionHost IP address.  This is the IP address that you must ssh to first before reaching the Riak nodes.

This stack can take around 20 minutes to build.  It will build the number of instances specified in RiakClusterSize, plus 1 NAT instance and 1 Bastion instance.


The filename for this receipe is **riak-vpc-cluster.json** .



## riak vpc cluster with appservers

This builds upon the riak-vpc-cluster with the addition of a set of load balanced application servers.  The application servers sit behind a public Elastic Load Balancer (ELB) and the make Riak api requests to an internal ELB responsible for the Riak Servers.  We are using a demo application called "Riagi" which is a simple image uploading tool to demonstrate the cluster.  This recipe has all the same options as riak-cluster-vpc plus the following:



* **FrontendClusterSize**
	* The number of ec2 instances that will make up the Frontend Cluster.
* **FrontendInstanceType**
	* The ec2 instance type of the Frontend instances.


Once the stack is completed, check the outputs of the stack to find the BastionIP address.  This is the IP address that you must ssh to first before reaching the Riak nodes.  It will build the number of instances specified in RiakClusterSize, FrontendClusterSize, 1 NAT instance, and 1 Bastion instance.

Also in the outputs you will find the Bastion Host IP and the Website URL to access Riagi.


The filename for this receipe is **riak-vpc-cluster-with-frontend-appservers.json** . 


