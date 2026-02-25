---
title: "Lets Talk Kubernetes - High Availability"
date: 2021-07-17
tags: 
  - "autoscaling"
  - "aws"
  - "devops"
  - "ha"
  - "high-availability"
  - "k8s"
  - "kubernetes"
---

## Overview

Some of the huge benefits to running kubernetes is to have a robust, scalable application and hopefully eliminate as much downtime as possible. But how exactly do you accomplish this? Kubernetes (k8s from here forward) has a lot of features right out of the box to ensure your application stays up and running as long as it's designed to properly leverage the features, however to have a truly scalable infrastructure things do get a little bit more involved. Today, we are going to go over, at a high level, some of the things that will help you design and build an infrastructure that is resilient, and leverages the scaling capabilities of k8s running in the cloud to enable your environment to stay up and running through any number of adverse conditions.

If you've been working around computer systems for any length of time, you have most likely heard the term "single point of failure" (SPoF) used at least a few times; it's a very common thing to worry about for business critical infrastructure and software. When setting up a highly available (HA) infrastructure, the idea is to find and eliminate as many single points of failure as possible. With that being said, lets dive in.

## First Things First

Before we can take advantage of these highly available setups, one of the most important things to be able to properly leverage the architecture is to ensure that your application can scale out with the infrastructure. I don't want this article to get too bloated, but understanding how to build a scalable web application is vital to the rest of what we are going to build here, so if you're not familiar with this concept, you may want to review some documentation on how to ensure your application can scale up properly. One industry standard that I frequently use is called "The 12 factor application", which I was originally made aware of while deploying using [Heroku](https://www.heroku.com/). The website [The Twelve-Factor App](https://12factor.net/) has a pretty good breakdown of the requirements, so if you're not familiar with the concept I would head over there and get yourself acquainted.

With that out of the way, lets move on to an overview of HA architecture with AWS.

## 3-Tier Cloud Infrastructure

3-Tier Infrastructure is one of the most popular ways to set up cloud infrastructure for HA capabilities. The basics are, as the name implies having 3 separate tiers of infrastructure:

- Public Layer
- Application Layer
- Database Layer

To fully understand everything we are going to go over here, please reference the following diagram, which is a reference architecture for 3-tier infrastructure on the AWS platform.

![AWS 3-tier Infrastructure Diagram](images/aws-3-tier-infrastructure-3a.png "AWS 3-tier Infrastructure Diagram")

### Public Layer

The public layer, as the name implies, are the resources that are accessible from the public internet. These resources are typically going to be a load balancer (either a Network LB or an Application LB) and a Bastion server, which is what you will use to manage all of your infrastructure that otherwise is not publicly accessible. Load balancers are referred to by different names across cloud providers, but all of them are going to be either network based, operating on Layer 4, or application based, operating on Layer 7 (see: [The OSI Model](https://www.forcepoint.com/cyber-edu/osi-model)) Just note that even though the cloud providers might have a specific name for their products, all of them will be one of these two types and largely function similarly under the hood.

The Public layer sits inside of a public subnet, and is therefore open to all internet traffic; Due to this any resources inside of this layer need special attention paid to them, because they constitute what is known as the perimeter, and is the first part of your infrastructure that potential attackers will focus on.

### Application Layer

The Application Layer is where your application servers live. If you are running a CMS such as Wordpress, Django, Ruby on Rails (RoR), or whatever you happen to use, this layer is where those application will sit and serve your web files. This is also the layer where you will typically wrap your application servers inside of an Autoscaling Group.

The Application layer sits inside of a private subnet, and is therefore not directly accessible from the internet, and usually cannot access the internet directly either; due to this you will want to set up a NAT Gateway, which is a cloud resource that allows resources inside of a private subnet to access the internet for application updates and things of that nature. Please note that this is different from an Internet Gateway, which allows internet access from your VPC, and typically sites outside of your VPC. A NAT gateway, however sits inside of your VPC.

The following diagram might help you visualize how each of these components interact:

### Database Layer

The 3rd layer is your Database Layer, which is where any database that backs your application sits. This layer does not have any public access, and should be limited to only allow resources in your Application Layer to access it, and only on the required ports your database instance requires.

## Notes

Each of the 3 layers should have both their own subnet, as well as their own security groups. The public subnet, containing your ELB and any bastion hosts, will be publicly accessible. The security groups operate on an instance level, not the network level, so you configure access based on the security group of other resources. The public security group should be configured with an inbound rule to allow all traffic.  
  
The other two tiers, the application and the database layers, will both sit inside of private subnets which are not accessible from the internet.

For the public layer, you will configure the security group to allow traffic from all sources (0.0.0.0) typically on ports 80, 443, and 22 (or 3389 for RDP instead of SSH).  
  
For the application layer, the security group will allow access from the ELB and bastion security groups to your application ports. This can be port 80 and 443, but oftentimes is not, and will depend on how the underlying application is configured to serve traffic. In addition, management ports (22 or 3389) should be configured to allow access from the public subnet and security group.  
  
The database layer will have it's own security group as well, and should be configured to only allow access from the application layer security group on the required database port (3306 for MySQL, 5432 for PostgreSQL) from the web subnet and security group.

If you are familiar with the aws api, a sample configuration of these groups could be setup with the following commands:

```

    ec2-authorize WebSG -P tcp -p 80 -s 0.0.0.0/0
    ec2-authorize WebSG -P tcp -p 443 -s 0.0.0.0/0
    ec2-authorize WebSG -P tcp -p 22|3389 -s CorpNet

    ec2-authorize AppSG -P tcp|udp -p AppPort|AppPort-Range -o WebSG
    ec2-authorize AppSG -P tcp -p 22|3389 -s CorpNet

    ec2-authorize DBSG -P tcp|udp -p DBPort|DBPort-Range -o AppSG
    ec2-authorize DBSG -P tcp -p 22|3389 -s CorpNet
    ec2-authorize DBSG -P tcp -p 22|3389 -s VendorNet

```

If you would like to dive deeper into this, you can check out the AWS provided documentation for creating security groups in reference to a 3-tier infrastructure [here](https://aws.amazon.com/blogs/aws/building-three-tier-architectures-with-security-groups/).

## Autoscaling

Scaling at the cloud provider level is accomplished using Autoscaling Groups, which function by having a set of servers inside of their "target group" and monitoring certain metrics; when one or more servers goes outside of the bounds of the metric limits you configure, the autoscaling group triggers a scaling event, which means using a pre-made image (for AWS, this would be an AMI) to spin up 1 or more new application servers. Once the new server or servers are ready, the LB uses Liveness Probes to ensure the application is ready to serve traffic, and once the Liveness Probe succeeds, the new resources are added to the load balancers pool. A Liveness Probe can be super simple, just checking if a port or range of ports is open for traffic (typically 80 and/or 443), but can get more complex, such as sending a request to a /status endpoint, which is a page created by the application developer(s) that does a number of checks on the web app to make sure certain features are ready and working properly.

## Putting it all together

We have now went over 3-tier infrastructure concepts, but how does it specifically apply to k8s? First it's important to understand that k8s scales in 3 different ways:

- Individual pods can scale, typically using the Horizontal Pod Autoscaler (HPA) or the Vertical Pod Autoscaler (VPA)
    - The HPA creates additional pods and then schedules them on an appropriate worker node
    - The VPA modifies the resource requests of the pods, increasing or decreasing the amount of resources the pod requests upon scheduling
- The nodes themselves will also need to scale to keep up with the workload of additional pods being added, and this can be either horizontal or vertical
    - Horizontal scaling is when more resources are spun up, and additional nodes are added to the load balancing pool
    - Vertical scaling, which utilizes the Vertical Pod Autoscaler (VPA) is when the nodes themselves are resized to have more resources, but the # of nodes does not change

The Cluster Autoscaler is configured with a provider that then utilizes the API of your given cloud provider to trigger the building of a new node (or multiple nodes in some cases); this type of trigger is sometimes referred to as an autoscaling event.

When configuring autoscaling it's important to note the difference between master, AKA control plane nodes, and worker nodes. The control plane nodes house services such as the REST API, the controllers, and etcd instances; the worker nodes run the pods where your application lives. The control plane nodes should be set up outside of your autoscaling group (ASG), or potentially in their own ASG, while the worker nodes will sit inside of it. On top of this, you should also note the difference at the cluster level between horizontal scaling and vertical scaling, which as noted above in regards to pod scaling, works much the same: vertical scaling is modifying the size of the nodes, whereas horizontal scaling is modifying the # of nodes in the cluster.

### Important Considerations - Resource Requests

One of the most important things to consider when utilizing the cluster autoscaling functions is that all of the nodes have a similar resource footprint, which basically just means the compute and memory capabilities are as similar as possible, if not exact replicas. This is due to the way k8s handles scaling, as it does so by creating a node template, and using that node template to ascertain how many nodes are needed to serve the pods that need scheduling.

Using the same node type is also advisable, although you can use different node types, if you do so you will want to keep the resource capabilities as similar as possible, as stated above.

Another extremely important thing is to make sure ALL of your pods have resource requests defined, and that they are as accurate as possible. Not having proper resources defined can cause a number of issues and will result in trouble during scaling events. The reason for this is based on how the cluster makes decisions on scaling events: Utilization is calculated as the sum of requested resources divided by the capacity of your worker nodes. As you can imagine, if your pods do not have resource requests defined, this formula will result in false calculations, which can lead to undesirable scaling events.

### Important Considerations - Permissions

Each cloud provider is going to have a different way of handling permissions, however their functionality is typically very similar. I will go over the permissions required for IAM roles using AWS, however if you look closely at the IAM permissions that are required, you should be able to determine what permissions are required for each individual role for GCE, Azure, or any other cloud environment.

When dealing with autoscaling events, the cluster is going to need access to a few things in the cloud provider. The cluster will need access to the autoscaling group so that it can read the current status of the cluster as well as make changes to it in order to bring the state of the cluster in line with the desired state. The cluster will also need access to read and write the Launch Configurations. To properly set this up, you are going to need (at least) 3 groups of profiles.  
1) A profile for the ASG. This profile should have access to the autoscaling functions as well as the launch templates for ec2:

```
        "autoscaling:DescribeAutoScalingGroups",
                "autoscaling:DescribeAutoScalingInstances",
                "autoscaling:DescribeLaunchConfigurations",
                "autoscaling:SetDesiredCapacity",
                "autoscaling:TerminateInstanceInAutoScalingGroup",
                "autoscaling:DescribeTags",
                "autoscaling:DescribeLaunchConfigurations",
                "ec2:DescribeLaunchTemplateVersions"
```

2) A profile for the master nodes. This group will have access to a few of the autoscaling group functions, the ec2 (servers), elb (elastic load balancer) functions, the ecr (elastic container registry), iam service account linking, and kms describe key permissions.

- Note 1: ECR permissions are only required if you are using AWS ecr, if you are utilizing an external container registry, these permissions are not required, and you will also need to perform some additional configuration to utilize your container registry.
- Note 2: KMS permissions are only required if you are using AWS kms, if you are using something else, such as Hashicorp Vault, the permissions aren't necessary but you will need to make sure your launch template and configurations have access to wherever your vault is running

```
        "autoscaling:DescribeAutoScalingGroups",
        "autoscaling:DescribeLaunchConfigurations",
        "autoscaling:DescribeTags",
        "ec2:DescribeInstances",
        "ec2:DescribeRegions",
        "ec2:DescribeRouteTables",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "ec2:DescribeVolumes",
        "ec2:CreateSecurityGroup",
        "ec2:CreateTags",
        "ec2:CreateVolume",
        "ec2:ModifyInstanceAttribute",
        "ec2:ModifyVolume",
        "ec2:AttachVolume",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:CreateRoute",
        "ec2:DeleteRoute",
        "ec2:DeleteSecurityGroup",
        "ec2:DeleteVolume",
        "ec2:DetachVolume",
        "ec2:RevokeSecurityGroupIngress",
        "ec2:DescribeVpcs",
        "elasticloadbalancing:AddTags",
        "elasticloadbalancing:AttachLoadBalancerToSubnets",
        "elasticloadbalancing:ApplySecurityGroupsToLoadBalancer",
        "elasticloadbalancing:CreateLoadBalancer",
        "elasticloadbalancing:CreateLoadBalancerPolicy",
        "elasticloadbalancing:CreateLoadBalancerListeners",
        "elasticloadbalancing:ConfigureHealthCheck",
        "elasticloadbalancing:DeleteLoadBalancer",
        "elasticloadbalancing:DeleteLoadBalancerListeners",
        "elasticloadbalancing:DescribeLoadBalancers",
        "elasticloadbalancing:DescribeLoadBalancerAttributes",
        "elasticloadbalancing:DetachLoadBalancerFromSubnets",
        "elasticloadbalancing:DeregisterInstancesFromLoadBalancer",
        "elasticloadbalancing:ModifyLoadBalancerAttributes",
        "elasticloadbalancing:RegisterInstancesWithLoadBalancer",
        "elasticloadbalancing:SetLoadBalancerPoliciesForBackendServer",
        "elasticloadbalancing:AddTags",
        "elasticloadbalancing:CreateListener",
        "elasticloadbalancing:CreateTargetGroup",
        "elasticloadbalancing:DeleteListener",
        "elasticloadbalancing:DeleteTargetGroup",
        "elasticloadbalancing:DescribeListeners",
        "elasticloadbalancing:DescribeLoadBalancerPolicies",
        "elasticloadbalancing:DescribeTargetGroups",
        "elasticloadbalancing:DescribeTargetHealth",
        "elasticloadbalancing:ModifyListener",
        "elasticloadbalancing:ModifyTargetGroup",
        "elasticloadbalancing:RegisterTargets",
        "elasticloadbalancing:SetLoadBalancerPoliciesOfListener",
        "iam:CreateServiceLinkedRole",
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:GetRepositoryPolicy",
        "ecr:DescribeRepositories",
        "ecr:ListImages",
        "ecr:BatchGetImage",
        "kms:DescribeKey"
`

  3) A profile for the worker nodes. This profile needs ec2 and ecr permissions.
```

json  
"ec2:DescribeInstances",  
"ec2:DescribeRegions",  
"ecr:GetAuthorizationToken",  
"ecr:BatchCheckLayerAvailability",  
"ecr:GetDownloadUrlForLayer",  
"ecr:GetRepositoryPolicy",  
"ecr:DescribeRepositories",  
"ecr:ListImages",  
"ecr:BatchGetImage"  
\`\`\`

## Conclusion

There is a decent amount of configuration that goes into setting up a proper autoscaling kubernetes cluster. While this will be quite a robust configuration in it's own right, in a later article we are going to go over a few additional pieces, such as ensuring the workloads get properly spread between Availability Zones (AZs) as well as some of the considerations that would come with deploying to multiple cloud providers.
