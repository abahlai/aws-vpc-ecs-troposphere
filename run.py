from troposphere import Ref, Template, Tags, Parameter, GetAtt
import troposphere.ec2 as ec2

cidr_vpc = '10.0.0.0/16'
cidr_subnet_pub = '10.0.0.0/24'
cidr_subnet_priv = '10.0.1.0/24'

template = Template()

vpcName = template.add_parameter(Parameter(
    'vpcName',
    Type="String"
))

natKeyName = template.add_parameter(Parameter(
    'natKeyName',
    Type="String"
))

natIP = template.add_parameter(Parameter(
    'natIP',
    Type="String"
))


vpc = template.add_resource(ec2.VPC(
    'myVpc',
    CidrBlock=cidr_vpc,
    Tags=Tags(
        Name=Ref(vpcName)
    )
))

vpcSecurityGroupDefault = template.add_resource(ec2.SecurityGroup(
    'vpcSecurityGroupDefault',
    VpcId=Ref(vpc),
    GroupDescription='default VPC security group'
))

template.add_resource(ec2.SecurityGroupIngress(
    'vpcSGDefaultIngressInsideVPC',
    GroupId=Ref(vpcSecurityGroupDefault),
    IpProtocol='-1'
))

template.add_resource(ec2.SecurityGroupEgress(
    'vpcSGDefaultEgress',
    GroupId=Ref(vpcSecurityGroupDefault),
    IpProtocol='-1',
    FromPort='-1',
    ToPort='-1',
    CidrIp='0.0.0.0/0'
))

internetGateway = template.add_resource(ec2.InternetGateway(
    'internetGateway'
))

vpcInternetGatewayAttachment = template.add_resource(ec2.VPCGatewayAttachment(
    'vpcInternetGateway',
    InternetGatewayId=Ref(internetGateway),
    VpcId=Ref(vpc)
))

subnetPub = template.add_resource(ec2.Subnet(
    'subnetPub',
    CidrBlock=cidr_subnet_pub,
    VpcId=Ref(vpc),
    Tags=Tags(
        Name="subnetPub"
    )
))

subnetPubRouteTable = template.add_resource(ec2.RouteTable(
    'subnetPubRouteTable',
    VpcId=Ref(vpc),
    Tags=Tags(
        VPC=Ref(vpcName)
    )
))

template.add_resource(ec2.SubnetRouteTableAssociation(
    'pubSubnetRouteTableAssociation',
    RouteTableId=Ref(subnetPubRouteTable),
    SubnetId=Ref(subnetPub)
))

template.add_resource(ec2.Route(
    'subletPrivInstanceNatRoute',
    RouteTableId=Ref(subnetPubRouteTable),
    DestinationCidrBlock='0.0.0.0/0',
    GatewayId=Ref(internetGateway),
    DependsOn=vpcInternetGatewayAttachment.title
))


subnetPriv = template.add_resource(ec2.Subnet(
    'subnetPriv',
    CidrBlock=cidr_subnet_priv,
    VpcId=Ref(vpc),
    Tags=Tags(
        Name='subnetPriv'
    )
))


subnetPrivRouteTable = template.add_resource(ec2.RouteTable(
    'subnetPrivRouteTable',
    VpcId=Ref(vpc),
    Tags=Tags(
        VPC=Ref(vpcName)
    )
))


template.add_resource(ec2.SubnetRouteTableAssociation(
    'subnetPugRouteTableAssociation',
    RouteTableId=Ref(subnetPrivRouteTable),
    SubnetId=Ref(subnetPriv)
))


instanceNAT = template.add_resource(ec2.Instance(
    'instanceNAT',
    ImageId='ami-7da94839',
    InstanceType='t2.micro',
    KeyName=Ref(natKeyName),
    NetworkInterfaces=[
        ec2.NetworkInterfaceProperty(
            'natNetworkInterface',
            Description='instaneNAT network interface',
            SubnetId=Ref(subnetPub),
            DeviceIndex=0,
            PrivateIpAddresses=[
                ec2.PrivateIpAddressSpecification(
                    'natPrivateIp',
                    Primary='true',
                    PrivateIpAddress=Ref(natIP),
                )
            ],
            GroupSet=[Ref(vpcSecurityGroupDefault)]
        )
    ]
))

instanceNATEIP = template.add_resource(ec2.EIP(
    'instanceNATEIP',
    DependsOn=vpcInternetGatewayAttachment.title
))

instanceNATEIPAssociation = template.add_resource(ec2.EIPAssociation(
    'instanceNATEIPAssociation',
    AllocationId=GetAtt(instanceNATEIP, 'AllocationId'),
    InstanceId=Ref(instanceNAT)
))

template.add_resource(ec2.Route(
    'subletPrivInatanceNateRoute',
    RouteTableId=Ref(subnetPrivRouteTable),
    DestinationCidrBlock='0.0.0.0/0',
    InstanceId=Ref(instanceNAT),
    DependsOn=instanceNAT.title
))

print(template.to_json())