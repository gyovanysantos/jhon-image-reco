import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';

export interface ScraperStackProps extends cdk.StackProps {
  dataBucket: s3.Bucket;
}

export class ScraperStack extends cdk.Stack {
  public readonly partsTable: dynamodb.Table;

  constructor(scope: Construct, id: string, props: ScraperStackProps) {
    super(scope, id, props);

    // DynamoDB table for part catalog data
    this.partsTable = new dynamodb.Table(this, 'PartsTable', {
      tableName: 'parts-catalog',
      partitionKey: { name: 'part_number', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
    });

    // ECR repository for scraper container
    const scraperRepo = new ecr.Repository(this, 'ScraperRepo', {
      repositoryName: 'jhon-image-reco-scraper',
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      emptyOnDelete: true,
    });

    // VPC for Fargate task
    const vpc = new ec2.Vpc(this, 'ScraperVpc', {
      maxAzs: 2,
      natGateways: 1,
    });

    // ECS Cluster
    const cluster = new ecs.Cluster(this, 'ScraperCluster', {
      vpc,
      clusterName: 'jhon-scraper-cluster',
    });

    // Fargate task definition
    const taskDefinition = new ecs.FargateTaskDefinition(this, 'ScraperTask', {
      memoryLimitMiB: 512,
      cpu: 256,
    });

    taskDefinition.addContainer('scraper', {
      image: ecs.ContainerImage.fromEcrRepository(scraperRepo),
      logging: ecs.LogDrivers.awsLogs({ streamPrefix: 'scraper' }),
      environment: {
        S3_BUCKET: props.dataBucket.bucketName,
        AWS_REGION: this.region,
      },
    });

    // Grant permissions
    props.dataBucket.grantReadWrite(taskDefinition.taskRole);
    this.partsTable.grantReadWriteData(taskDefinition.taskRole);

    // Outputs
    new cdk.CfnOutput(this, 'PartsTableName', { value: this.partsTable.tableName });
    new cdk.CfnOutput(this, 'ScraperRepoUri', { value: scraperRepo.repositoryUri });
    new cdk.CfnOutput(this, 'ClusterName', { value: cluster.clusterName });
  }
}
