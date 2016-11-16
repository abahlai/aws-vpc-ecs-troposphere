from troposphere import (
    Template,
    iam,
    AWS_REGION,
    AWS_STACK_ID,
    AWS_STACK_NAME,
    autoscaling,
    Base64,
    cloudformation,
    FindInMap,
    Join,
    Parameter,
    Ref,
    GetAtt,
)

from troposphere.ec2 import (
    EIP,
    InternetGateway,
    NatGateway,
    Route,
    RouteTable,
    Subnet,
    SubnetRouteTableAssociation,
    VPC,
    VPCGatewayAttachment,
    SecurityGroup,
    SecurityGroupRule,
)

from troposphere.ecs import (
    Cluster,
)

# The CloudFormation template
template = Template()

#==========VPC Section==========//
vpc = VPC(
    "Vpc",
    template=template,
    CidrBlock="10.0.0.0/16",
)


# Allow outgoing to outside VPC
internet_gateway = InternetGateway(
    "InternetGateway",
    template=template,
)


# Attach Gateway to VPC
VPCGatewayAttachment(
    "GatewayAttachement",
    template=template,
    VpcId=Ref(vpc),
    InternetGatewayId=Ref(internet_gateway),
)


# Public route table
public_route_table = RouteTable(
    "PublicRouteTable",
    template=template,
    VpcId=Ref(vpc),
)


public_route = Route(
    "PublicRoute",
    template=template,
    GatewayId=Ref(internet_gateway),
    DestinationCidrBlock="0.0.0.0/0",
    RouteTableId=Ref(public_route_table),
)


# Holds public instances
public_subnet_cidr = "10.0.1.0/24"

public_subnet = Subnet(
    "PublicSubnet",
    template=template,
    VpcId=Ref(vpc),
    CidrBlock=public_subnet_cidr,
)


SubnetRouteTableAssociation(
    "PublicSubnetRouteTableAssociation",
    template=template,
    RouteTableId=Ref(public_route_table),
    SubnetId=Ref(public_subnet),
)

# NAT
natinstancetype_param = template.add_parameter(Parameter(
    "NatInstanceType",
    Description="NAT InstanceType",
    Default="t1.micro",
    Type="String",
    ))

natimageid_param = template.add_parameter(Parameter(
    "NatImageId",
    Description="NAT ImageId",
    Default="ami-030f4133",
    Type="String",
    ))

natkeyname_param = template.add_parameter(Parameter(
    "NatKeyName",
    Description="NAT KeyName",
    Default="keysfortesting",
    Type="String",
    ))

	
NatEIP = template.add_resource(EIP(
    "NatEIP",
    InstanceId=Ref("Nat"),
    Domain="vpc",
))


Nat = template.add_resource(Instance(
    "Nat",
    SourceDestCheck="false",
#    SecurityGroupIds=[Ref(NatSG)],
    KeyName=Ref(natkeyname_param),
    SubnetId=Ref(public_subnet),
    ImageId=Ref(natimageid_param),
    InstanceType=Ref(natinstancetype_param),
#    Tags=Tags(
#        Name=Join("",[Ref("AWS::StackName"),"-nat"]),
#    )
))	
	
	
# Private route table
private_route_table = RouteTable(
    "PrivateRouteTable",
    template=template,
    VpcId=Ref(vpc),
)


private_nat_route = Route(
    "PrivateNatRoute",
    template=template,
    RouteTableId=Ref(private_route_table),
    DestinationCidrBlock="0.0.0.0/0",
    InstanceId=Ref("Nat"),
)


# Holds containers instances
container_a_subnet_cidr = "10.0.10.0/24"
container_a_subnet = Subnet(
    "ContainerASubnet",
    template=template,
    VpcId=Ref(vpc),
    CidrBlock=container_a_subnet_cidr,
    AvailabilityZone=Join("", [Ref(AWS_REGION), "a"]),
)


SubnetRouteTableAssociation(
    "ContainerARouteTableAssociation",
    template=template,
    SubnetId=Ref(container_a_subnet),
    RouteTableId=Ref(private_route_table),
)


container_b_subnet_cidr = "10.0.11.0/24"
container_b_subnet = Subnet(
    "ContainerBSubnet",
    template=template,
    VpcId=Ref(vpc),
    CidrBlock=container_b_subnet_cidr,
    AvailabilityZone=Join("", [Ref(AWS_REGION), "b"]),
)


SubnetRouteTableAssociation(
    "ContainerBRouteTableAssociation",
    template=template,
    SubnetId=Ref(container_b_subnet),
    RouteTableId=Ref(private_route_table),
)

#==========Container Section==========//

# ECS cluster
cluster = Cluster(
    "Cluster",
    template=template,
)

# ECS container role
container_instance_role = iam.Role(
    "ContainerInstanceRole",
    template=template,
    AssumeRolePolicyDocument=dict(Statement=[dict(
        Effect="Allow",
        Principal=dict(Service=["ec2.amazonaws.com"]),
        Action=["sts:AssumeRole"],
    )]),
    Path="/",
    Policies=[
        iam.Policy(
            PolicyName="ECSManagementPolicy",
            PolicyDocument=dict(
                Statement=[dict(
                    Effect="Allow",
                    Action=[
                        "ecs:*",
#                        "elasticloadbalancing:*",
                    ],
                    Resource="*",
                )],
            ),
        ),
    ]
)


# ECS container instance profile
container_instance_profile = iam.InstanceProfile(
    "ContainerInstanceProfile",
    template=template,
    Path="/",
    Roles=[Ref(container_instance_role)],
)

#==========AutoScaling LaunchConf==========//

container_instance_type = Ref(template.add_parameter(Parameter(
    "ContainerInstanceType",
    Description="The container instance type",
    Type="String",
    Default="t2.micro",
    AllowedValues=["t2.micro", "t2.small", "t2.medium"]
)))


template.add_mapping("ECSRegionMap", {
    "eu-west-1": {"AMI": "ami-4e6ffe3d"},
    "us-east-1": {"AMI": "ami-8f7687e2"},
    "us-west-2": {"AMI": "ami-84b44de4"},
})


container_instance_configuration_name = "ContainerLaunchConfiguration"


container_instance_configuration = autoscaling.LaunchConfiguration(
    container_instance_configuration_name,
    template=template,
    Metadata=autoscaling.Metadata(
        cloudformation.Init(dict(
            config=cloudformation.InitConfig(
                commands=dict(
                    register_cluster=dict(command=Join("", [
                        "#!/bin/bash\n",
                        # Register the cluster
                        "echo ECS_CLUSTER=",
                        Ref(cluster),
                        " >> /etc/ecs/config\n",
                    ]))
                ),
                files=cloudformation.InitFiles({
                    "/etc/cfn/cfn-hup.conf": cloudformation.InitFile(
                        content=Join("", [
                            "[main]\n",
                            "template=",
                            Ref(AWS_STACK_ID),
                            "\n",
                            "region=",
                            Ref(AWS_REGION),
                            "\n",
                        ]),
                        mode="000400",
                        owner="root",
                        group="root",
                    ),
                    "/etc/cfn/hooks.d/cfn-auto-reload.conf":
                    cloudformation.InitFile(
                        content=Join("", [
                            "[cfn-auto-reloader-hook]\n",
                            "triggers=post.update\n",
                            "path=Resources.%s."
                            % container_instance_configuration_name,
                            "Metadata.AWS::CloudFormation::Init\n",
                            "action=/opt/aws/bin/cfn-init -v ",
                            "         --template ",
                            Ref(AWS_STACK_NAME),
                            "         --resource %s"
                            % container_instance_configuration_name,
                            "         --region ",
                            Ref("AWS::Region"),
                            "\n",
                            "runas=root\n",
                        ])
                    )
                }),
                services=dict(
                    sysvinit=cloudformation.InitServices({
                        'cfn-hup': cloudformation.InitService(
                            enabled=True,
                            ensureRunning=True,
                            files=[
                                "/etc/cfn/cfn-hup.conf",
                                "/etc/cfn/hooks.d/cfn-auto-reloader.conf",
                            ]
                        ),
                    })
                )
            )
        ))
    ),
#    SecurityGroups=[Ref(container_security_group)],
    InstanceType=container_instance_type,
    ImageId=FindInMap("ECSRegionMap", Ref(AWS_REGION), "AMI"),
    IamInstanceProfile=Ref(container_instance_profile),
    UserData=Base64(Join('', [
        "#!/bin/bash -xe\n",
        "yum install -y aws-cfn-bootstrap\n",

        "/opt/aws/bin/cfn-init -v ",
        "         --template ", Ref(AWS_STACK_NAME),
        "         --resource %s " % container_instance_configuration_name,
        "         --region ", Ref(AWS_REGION), "\n",
    ])),
)

#==========AutoScaling Section==========//

max_container_instances = Ref(template.add_parameter(Parameter(
    "MaxScale",
    Description="Maximum container instances count",
    Type="Number",
    Default="3",
)))

desired_container_instances = Ref(template.add_parameter(Parameter(
    "DesiredScale",
    Description="Desired container instances count",
    Type="Number",
    Default="3",
)))


autoscaling_group_name = "AutoScalingGroup"


autoscaling_group = autoscaling.AutoScalingGroup(
    autoscaling_group_name,
    template=template,
    VPCZoneIdentifier=[Ref(container_a_subnet), Ref(container_b_subnet)],
    MinSize=desired_container_instances,
    MaxSize=max_container_instances,
    DesiredCapacity=desired_container_instances,
    LaunchConfigurationName=Ref(container_instance_configuration),
#    LoadBalancerNames=[Ref(load_balancer)],
    # Since one instance within the group is a reserved slot
    # for rolling ECS service upgrade, it's not possible to rely
    # on a "dockerized" `ELB` health-check, else this reserved
    # instance will be flagged as `unhealthy` and won't stop respawning'
    HealthCheckType="EC2",
    HealthCheckGracePeriod=300,
)

print(template.to_json())