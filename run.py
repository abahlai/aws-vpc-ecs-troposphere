from troposphere import Ref, Template, Tags, Parameter, GetAtt
import troposphere.ec2 as ec2

cidr_vpc = '10.0.0.0/16'

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

template.add_resource(ec2.SecurityGroupIngress(
    'vpcSGDefaultIngressSSH',
    GroupId=Ref(vpcSecurityGroupDefault),
    IpProtocol='-1',
    FromPort='-1',
    ToPort='22',
    CidrIp='0.0.0.0/0'
))

template.add_resource(ec2.SecurityGroupEgress(
    'vpcSGDefaultEgress',
    GroupId=Ref(vpcSecurityGroupDefault),
    IpProtocol='-1',
    FromPort='-1',
    ToPort='-1',
    CidrIp='0.0.0.0/0'
))

print(template.to_json())