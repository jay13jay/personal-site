---
title: "Lets Talk Kubernetes - Kubectl (Part 2 - Contexts and Output filtering)"
draft: true
---

So you have finally wrapped your head around the Kubernetes infrastructure. Today we're going to go over working with Contexts, and how to use output filtering to get specific information from kubectl.  

## Contexts

One significant, and potentially quite annoying difference when moving from lab environments you learn Kubernetes with into more robust production environments is going to be dealing with multiple, sometimes quite a few, contexts. One common practice you will see in almost every software shop is having multiple environments, at minimum a "Production" and "Development", and a lot of the time also a "Staging" and/or "Testing" environment as well - in the Kubernetes (k8s) ecosystem this manifests in creating a cluster per environment. You could also use namespaces to separate your environments, but this gets super messy. So what does this look like in practice?

```bash
jay@Joshs-MBP ~ % kubectl config get-contexts
CURRENT   NAME               CLUSTER      AUTHINFO                                NAMESPACE
          volos-k8s         volos-k8s   admVolos_prod_k8s
*         minikube          minikube    minikube                                cockroach-operator-system
          dev-volos-k8s     qa-k8s      admVolos_dev_k8s
          stage-volos-k8s   stage-k8s   admVolos_stage_k8s
```

What exactly are we looking at? Good question, and I know it can seem a little ambiguous, so lets break it down barney style:  
\- CURRENT: marks the context that kubectl is currently configured to use  
\- NAME: Name of the context. Please note that this is \*not\* the name of the cluster, and there is a difference  
\- CLUSTER: This is the name of the cluster, and as stated above is \*not\* the same as the NAME value for the context  
\- AUTHINFO: The configured user to auth with the cluster  
\- NAMESPACE: The contexts configured namespace

In the output above, I have one context configured per cluster but this is where the difference between the cluster name and the context name becomes important: you can configure multiple contexts on the same cluster if you want to.  
  
In my opinion, the most useful reason you would want to have multiple contexts on one cluster is to have one configured with a standard user for troubleshooting and gathering information, and another that can make changes to the deployed resources.  
Another reason you may want to do this is to work with one workload, for instance, a typical database-driven microservice application will have a number of microservices that gather data and populate the database which I like to call "runners". In the instance of a product tracking application, there are quite a few runners executing at any given time, and they all perform slightly different, but inherently related, tasks; this is the perfect use-case for a namespace. You can configure your contexts to talk with resources on a specific namespace, so using them together can make dealing with complex resources a little easier.  
Another use-case for a namespace that I personally use is to keep related services of a stateful set in their own namespace, for instance when running CockroachDB in K8s.  
  
When running Cockroach, you typically launch the management operator, and then launch the stateful set, and then you have an option of launching a client pod to securely connect, or more advisably using the client pod as an ephemeral tool and deleting it when not in use. To make life easier when managing cockroach, it's best to put all of these in a CRDB specific namespace; but then do you really have to pass in `-n cockroach-operator-system` every time you want to check the logs, or spin up the client pod? Turns out, nope: because the context is the concatenation of the cluster, the user, and the namespace, you can set any one of these values in the context itself, and then kubectl will use those settings.

To change context on the fly:

```bash
# First, get your namespaces and make sure you have the correct name
jay@Joshs-MBP ~ % kubectl get namespaces
NAME                        STATUS   AGE
cockroach-operator-system   Active   41h
default                     Active   2d10h
kube-node-lease             Active   2d10h
kube-public                 Active   2d10h
kube-system                 Active   2d10h
kubernetes-dashboard        Active   44h

# Then, check our current context:
jay@Joshs-MBP ~ % kubectl config get-contexts minikube
CURRENT   NAME       CLUSTER    AUTHINFO   NAMESPACE
*         minikube   minikube   minikube   default

# Change context to the CRDB namespace
jay@Joshs-MBP ~ % kubectl config set-context --current --namespace cockroach-operator-system
Context "minikube" modified.

# Check the context to see the change
jay@Joshs-MBP ~ % kubectl config get-contexts minikube
CURRENT   NAME       CLUSTER    AUTHINFO   NAMESPACE
*         minikube   minikube   minikube   cockroach-operator-system

```

If you make informed choices when setting up your Kubernetes cluster and keep logically distinct resources contained to their own namespace, it can make interacting with your cluster a lot easier. Due to CRDB being in its own namespace, it's now quite easy for us to get a nice overview of everything that goes with the services by running `kubectl get all`, which will output all resources in the namespace:

```bash
jay@Joshs-MBP ~ % kubectl get all
NAME                                              READY   STATUS    RESTARTS   AGE
pod/cockroach-operator-manager-5f64f48646-9jqs7   1/1     Running   0          41h
pod/cockroachdb-0                                 1/1     Running   0          41h
pod/cockroachdb-1                                 1/1     Running   0          41h
pod/cockroachdb-2                                 1/1     Running   0          41h
pod/cockroachdb-client-secure                     1/1     Running   0          41h

NAME                                         TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                        AGE
service/cockroach-operator-webhook-service   ClusterIP   10.110.144.127   <none>        443/TCP                        41h
service/cockroachdb                          ClusterIP   None             <none>        26258/TCP,8080/TCP,26257/TCP   41h
service/cockroachdb-public                   ClusterIP   10.110.168.45    <none>        26258/TCP,8080/TCP,26257/TCP   41h

NAME                                         READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/cockroach-operator-manager   1/1     1            1           41h

NAME                                                    DESIRED   CURRENT   READY   AGE
replicaset.apps/cockroach-operator-manager-5f64f48646   1         1         1       41h

NAME                           READY   AGE
statefulset.apps/cockroachdb   3/3     41h

NAME                                             AGE
crdbcluster.crdb.cockroachlabs.com/cockroachdb   41h
```

## Output Filtering

One of the things you may find you want to do frequently is to filter the output of kubectl, and there are a few different ways to do that depending on what you want to do.  
  
Quick-and-Dirty  
The most basic output filtering you will do is to get quick and dirty information. If the output is for human consumption, not a program, it doesn't need to be perfect, just easier to read, so using grep, awk, and sed can be quite useful.  
  
grep is used to search for a string on a per-line basis, so it's great for searching for a specific pod, IP address, and things of that nature. For instance, if you wanted to know what pods were running on a specific node, you could run:

```bash
# Get a count of the number of pods on node "minikube"
jay@Joshs-MBP ~ % kubectl get pods -o wide --all-namespaces | grep minikube |wc -l
      16

# List all of the pod names which are running on node "minikube" with their IP address
jay@Joshs-MBP ~ % kubectl get pods -o wide --all-namespaces | awk '/minikube/ {print $7,$2}'
172.17.0.2 cockroach-operator-manager-5f64f48646-9jqs7
172.17.0.7 cockroachdb-0
172.17.0.6 cockroachdb-1
172.17.0.8 cockroachdb-2
172.17.0.5 cockroachdb-client-secure
172.17.0.12 cockroachdb-client-secure
172.17.0.3 coredns-64897985d-j6nmn
192.168.64.4 etcd-minikube
192.168.64.4 kube-apiserver-minikube
192.168.64.4 kube-controller-manager-minikube
192.168.64.4 kube-proxy-j5d5g
192.168.64.4 kube-scheduler-minikube
172.17.0.10 metrics-server-6b76bd68b6-6wzln
192.168.64.4 storage-provisioner
172.17.0.11 dashboard-metrics-scraper-58549894f-p62sx
172.17.0.4 kubernetes-dashboard-ccd587f44-8wtsf
```

The `-o wide` is to print extra information columns in the output, namely the node and IP address, but it also displays the status on readiness gates and the nominated node. This is a VERY powerful troubleshooting tool, especially if you ever run into an issue (you will) where one or a few nodes are having issues that the rest of the cluster isn't; when that starts happening it's crucial to be able to selectively target individual nodes in your troubleshooting efforts.  
  
Once you have the extra output with -o you can then start filtering it with awk. You can customize this command quite extensively once you get what it's doing:  
awk '/minikube/ {print $7,$2}'  
The statement begins with an opening quote, and then an optional regex search term enclosed in //. You can omit the search term to get all output by changing it to awk '{print $7,$2}' instead.  
Inside of the brackets, the print statement can be formatted by passing in any arbitrary column number, in this case, columns 7 for the IP address, and column 2 for the pod name. By default, awk uses whitespace as a field separator, but if you wanted to change it to, say, a comma, (for instance, to parse CSV output) you would use: `awk -F","`  
Note: awk columns start at 1, not 0, this catches a lot of people out, so bear it in mind when counting out your columns
