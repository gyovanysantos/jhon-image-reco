import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as opensearchserverless from 'aws-cdk-lib/aws-opensearchserverless';
import { Construct } from 'constructs';

export interface VectorStackProps extends cdk.StackProps {
  dataBucket: s3.IBucket;
}

export class VectorStack extends cdk.Stack {
  public readonly opensearchEndpoint: string;

  constructor(scope: Construct, id: string, props: VectorStackProps) {
    super(scope, id, props);

    const collectionName = 'parts-vectors';

    // OpenSearch Serverless encryption policy
    new opensearchserverless.CfnSecurityPolicy(this, 'EncryptionPolicy', {
      name: 'parts-vectors-enc',
      type: 'encryption',
      policy: JSON.stringify({
        Rules: [{ ResourceType: 'collection', Resource: [`collection/${collectionName}`] }],
        AWSOwnedKey: true,
      }),
    });

    // OpenSearch Serverless network policy
    new opensearchserverless.CfnSecurityPolicy(this, 'NetworkPolicy', {
      name: 'parts-vectors-net',
      type: 'network',
      policy: JSON.stringify([
        {
          Rules: [
            { ResourceType: 'collection', Resource: [`collection/${collectionName}`] },
            { ResourceType: 'dashboard', Resource: [`collection/${collectionName}`] },
          ],
          AllowFromPublic: true,
        },
      ]),
    });

    // OpenSearch Serverless collection (vector search type)
    const collection = new opensearchserverless.CfnCollection(this, 'VectorCollection', {
      name: collectionName,
      type: 'VECTORSEARCH',
      description: 'Vector embeddings for HVAC part images',
    });

    this.opensearchEndpoint = collection.attrCollectionEndpoint;

    // Vectorization Lambda
    const vectorizeFn = new lambda.Function(this, 'VectorizeFn', {
      functionName: 'jhon-vectorize-images',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'vectorize_images.handler',
      code: lambda.Code.fromAsset('../functions'),
      timeout: cdk.Duration.minutes(5),
      memorySize: 512,
      environment: {
        OPENSEARCH_ENDPOINT: collection.attrCollectionEndpoint,
        INDEX_NAME: 'part-images',
      },
    });

    // Grant S3 read access via IAM policy (avoids cross-stack cyclic ref)
    vectorizeFn.addToRolePolicy(new iam.PolicyStatement({
      actions: ['s3:GetObject', 's3:ListBucket'],
      resources: [props.dataBucket.bucketArn, `${props.dataBucket.bucketArn}/*`],
    }));

    // Grant Bedrock access
    vectorizeFn.addToRolePolicy(new iam.PolicyStatement({
      actions: ['bedrock:InvokeModel'],
      resources: ['*'],
    }));

    // Grant OpenSearch Serverless access
    new opensearchserverless.CfnAccessPolicy(this, 'DataAccessPolicy', {
      name: 'parts-vectors-access',
      type: 'data',
      policy: JSON.stringify([
        {
          Rules: [
            {
              ResourceType: 'collection',
              Resource: [`collection/${collectionName}`],
              Permission: ['aoss:*'],
            },
            {
              ResourceType: 'index',
              Resource: [`index/${collectionName}/*`],
              Permission: ['aoss:*'],
            },
          ],
          Principal: [vectorizeFn.role!.roleArn],
        },
      ]),
    });

    // NOTE: S3 event trigger removed to avoid cross-stack cyclic dependency.
    // Vectorization is done via batch script (scripts/batch_vectorize.py) instead.

    // Outputs
    new cdk.CfnOutput(this, 'OpenSearchEndpoint', { value: collection.attrCollectionEndpoint });
    new cdk.CfnOutput(this, 'VectorizeFunctionName', { value: vectorizeFn.functionName });
  }
}
