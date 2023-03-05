import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_autoscaling as autoscaling
import aws_cdk.aws_elasticloadbalancingv2 as elbv2
from aws_cdk import Stack, aws_logs
from constructs import Construct

class Ec2WebStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Key for SSH
        prod_key = "proxy-1"

        vpc = ec2.Vpc(self, "MyVpc",
            nat_gateways=1
            )

        # UserData for Apache web server upon instance start
        multipart_user_data = ec2.MultipartUserData()
        commands_user_data = ec2.UserData.for_linux()
        multipart_user_data.add_user_data_part(commands_user_data, ec2.MultipartBody.SHELL_SCRIPT, True)

        multipart_user_data.add_commands("sudo yum update -y")
        multipart_user_data.add_commands("sudo amazon-linux-extras install php8.0 mariadb10.5")
        multipart_user_data.add_commands("cat /etc/system-release")
        multipart_user_data.add_commands("sudo yum install -y httpd")
        multipart_user_data.add_commands("sudo service httpd start")


        # Defines ec2 ASG, with Apache-installation userdata
        my_auto_scaling_group = autoscaling.AutoScalingGroup(self, "ASG",
            vpc=vpc,
            user_data=multipart_user_data,
            machine_image=ec2.AmazonLinuxImage(),
            key_name=prod_key,
            instance_type=ec2.InstanceType(instance_type_identifier="t2.nano"),
        )

        #
        application_target_group = elbv2.ApplicationTargetGroup(self, "TG1",
            target_type=elbv2.TargetType.INSTANCE,
            port=80,
            vpc=vpc
        )

        # Connects ASG to application_target_group
        my_auto_scaling_group.attach_to_application_target_group(application_target_group)

        # Instantiates basic Load Balancer
        lb = elbv2.ApplicationLoadBalancer(self, "LB",
            vpc=vpc,
            internet_facing=True
        )
        # Defines LB listener with application_target_group as target
        listener = lb.add_listener("listener",
            port=80
        )
        listener.add_target_groups("add_target_groups_id",
            target_groups=[application_target_group]
        )
