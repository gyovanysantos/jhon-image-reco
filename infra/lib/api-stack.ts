import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

export interface ApiStackProps extends cdk.StackProps {
  partsTable: dynamodb.Table;
  dataBucket: s3.IBucket;
}

export class ApiStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: ApiStackProps) {
    super(scope, id, props);

    // Recognition Lambda — vectorizes query image via Bedrock,
    // then computes cosine similarity against embeddings stored in DynamoDB
    const recognizeFn = new lambda.Function(this, 'RecognizeFn', {
      functionName: 'jhon-recognize',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'recognize_handler.handler',
      code: lambda.Code.fromAsset('../functions'),
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      environment: {
        TABLE_NAME: props.partsTable.tableName,
        BEDROCK_REGION: 'us-east-1',
      },
    });

    // Parts lookup Lambda
    const partsFn = new lambda.Function(this, 'PartsFn', {
      functionName: 'jhon-parts',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'parts_handler.handler',
      code: lambda.Code.fromAsset('../functions'),
      timeout: cdk.Duration.seconds(10),
      memorySize: 256,
      environment: {
        TABLE_NAME: props.partsTable.tableName,
      },
    });

    // Permissions
    props.partsTable.grantReadData(recognizeFn);
    props.partsTable.grantReadData(partsFn);

    recognizeFn.addToRolePolicy(new iam.PolicyStatement({
      actions: ['bedrock:InvokeModel'],
      resources: ['*'],
    }));

    // API Gateway
    const api = new apigateway.RestApi(this, 'PartsApi', {
      restApiName: 'HVAC Parts Recognition API',
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type'],
      },
    });

    // POST /api/recognize
    const apiResource = api.root.addResource('api');
    const recognizeResource = apiResource.addResource('recognize');
    recognizeResource.addMethod('POST', new apigateway.LambdaIntegration(recognizeFn));

    // GET /api/parts/{part_number}
    const partsResource = apiResource.addResource('parts');
    const partNumberResource = partsResource.addResource('{part_number}');
    partNumberResource.addMethod('GET', new apigateway.LambdaIntegration(partsFn));

    // Outputs
    new cdk.CfnOutput(this, 'ApiUrl', {
      value: api.url,
      description: 'API Gateway URL',
    });
  }
}
