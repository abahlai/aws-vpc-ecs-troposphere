from troposphere import Ref, Template, Tags, Parameter
import troposphere.ec2 as ec2

cidr_vpc = '10.0.0.0/16'
cidr_subnet_pub = '10.0.0.0/24'
cidr_subnet_priv = '10.0.1.0/24'

template = Template()

vpcName = template.add_parameter(Parameter(
    'vpcName',
    Type="String"
))

vpc = template.add_resource(ec2.VPC(
    'myVpc',
    CidrBlock=cidr_vpc,
    Tags=Tags(
        Name=Ref(vpcName)
    )
))

internetGateway = template.add_resource(ec2.InternetGateway(
    'internetGateway',
    Tags=Tags(
        VPC=Ref(vpcName)
    )
))

template.add_resource(ec2.VPCGatewayAttachment(
    'vpcInternetGateway',
    VpcId=Ref(vpc)
))

subnet_pub = template.add_resource(ec2.Subnet(
    'subnetPub',
    CidrBlock=cidr_subnet_pub,
    Tags=Tags(
        Name='subnetPub'
    ),
    VpcId=Ref(vpc)
))

subnet_priv = template.add_resource(ec2.Subnet(
    'subnetPriv',
    CidrBlock=cidr_subnet_priv,
    Tags=Tags(
        Name='subnetPriv'
    ),
    VpcId=Ref(vpc)
))


print(template.to_json())