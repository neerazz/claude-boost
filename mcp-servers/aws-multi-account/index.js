#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { exec } from "child_process";
import { promisify } from "util";
import fs from "fs/promises";
import os from "os";
import path from "path";

const execAsync = promisify(exec);

const server = new Server(
  {
    name: "aws-multi-account",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Parse AWS config to get all profiles
async function getAwsProfiles() {
  try {
    const configPath = path.join(os.homedir(), ".aws", "config");
    const content = await fs.readFile(configPath, "utf-8");

    const profiles = [];
    const profileRegex = /\[profile ([^\]]+)\]|^\[default\]/gm;
    let match;

    while ((match = profileRegex.exec(content)) !== null) {
      if (match[0] === '[default]') {
        profiles.push('default');
      } else if (match[1]) {
        profiles.push(match[1]);
      }
    }

    return profiles;
  } catch (error) {
    console.error("Error reading AWS config:", error);
    return [];
  }
}

// Parse AWS config to get account information
async function getAccountInfo() {
  try {
    const configPath = path.join(os.homedir(), ".aws", "config");
    const content = await fs.readFile(configPath, "utf-8");

    const accounts = {};
    const lines = content.split('\n');
    let currentProfile = null;

    for (const line of lines) {
      const profileMatch = line.match(/\[profile ([^\]]+)\]|^\[default\]/);
      if (profileMatch) {
        currentProfile = profileMatch[0] === '[default]' ? 'default' : profileMatch[1];
        accounts[currentProfile] = {};
      } else if (currentProfile) {
        const accountMatch = line.match(/sso_account_id\s*=\s*(\d+)/);
        const roleMatch = line.match(/sso_role_name\s*=\s*(.+)/);
        const regionMatch = line.match(/region\s*=\s*(.+)/);

        if (accountMatch) accounts[currentProfile].accountId = accountMatch[1].trim();
        if (roleMatch) accounts[currentProfile].role = roleMatch[1].trim();
        if (regionMatch) accounts[currentProfile].region = regionMatch[1].trim();
      }
    }

    return accounts;
  } catch (error) {
    console.error("Error parsing AWS config:", error);
    return {};
  }
}

// Execute AWS CLI command
async function executeAwsCommand(profile, command, timeout = 30000) {
  try {
    const fullCommand = profile === 'default'
      ? `aws ${command}`
      : `aws --profile ${profile} ${command}`;

    const { stdout, stderr } = await execAsync(fullCommand, {
      timeout,
      maxBuffer: 10 * 1024 * 1024 // 10MB buffer
    });

    if (stderr && !stderr.includes('Warning')) {
      return { success: false, error: stderr, profile };
    }

    return { success: true, output: stdout, profile };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      profile,
      stderr: error.stderr
    };
  }
}

// Execute command across all profiles
async function executeAcrossAllProfiles(command, filterProfiles = null) {
  const profiles = await getAwsProfiles();
  const accountInfo = await getAccountInfo();

  const profilesToQuery = filterProfiles
    ? profiles.filter(p => filterProfiles.includes(p))
    : profiles;

  const results = await Promise.all(
    profilesToQuery.map(profile => executeAwsCommand(profile, command))
  );

  return results.map(result => ({
    ...result,
    accountId: accountInfo[result.profile]?.accountId,
    role: accountInfo[result.profile]?.role,
    region: accountInfo[result.profile]?.region,
  }));
}

// List tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "list_aws_profiles",
        description: "List all configured AWS profiles with their account IDs and roles",
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
      {
        name: "execute_aws_command",
        description: "Execute an AWS CLI command on a specific profile or account",
        inputSchema: {
          type: "object",
          properties: {
            profile: {
              type: "string",
              description: "AWS profile name (e.g., 'vineet/backend-engineer', 'default')",
            },
            command: {
              type: "string",
              description: "AWS CLI command without 'aws' prefix (e.g., 's3 ls', 'ec2 describe-instances --region us-east-1')",
            },
            timeout: {
              type: "number",
              description: "Command timeout in milliseconds (default: 30000)",
            },
          },
          required: ["profile", "command"],
        },
      },
      {
        name: "query_all_accounts",
        description: "Execute an AWS CLI command across all configured accounts and aggregate results",
        inputSchema: {
          type: "object",
          properties: {
            command: {
              type: "string",
              description: "AWS CLI command without 'aws' prefix (e.g., 's3 ls', 'ec2 describe-instances --region us-east-1')",
            },
            filter_profiles: {
              type: "array",
              items: { type: "string" },
              description: "Optional list of profile names to filter (if not provided, queries all profiles)",
            },
          },
          required: ["command"],
        },
      },
      {
        name: "get_resource_summary",
        description: "Get a summary of specific AWS resources across all accounts in parallel",
        inputSchema: {
          type: "object",
          properties: {
            resource_type: {
              type: "string",
              enum: [
                "s3", "ec2", "rds", "lambda", "vpc", "ecs", "iam-roles",
                "ecr", "cloudwatch-logs", "sns", "sqs", "dynamodb",
                "apigateway", "cloudfront", "route53", "secrets-manager",
                "ssm-parameters", "kms", "security-hub", "guardduty",
                "iam-users", "iam-policies", "elb", "alb", "autoscaling",
                "cloudformation", "stepfunctions", "eventbridge", "kinesis",
                "elasticache", "opensearch", "redshift", "emr", "glue",
                "athena", "sagemaker", "codepipeline", "codebuild",
                "efs", "fsx", "backup", "acm", "waf", "shield"
              ],
              description: "Type of resource to summarize",
            },
            region: {
              type: "string",
              description: "AWS region (default: us-east-1)",
            },
          },
          required: ["resource_type"],
        },
      },
      {
        name: "get_all_resources",
        description: "Get ALL AWS resources across all accounts in parallel - comprehensive infrastructure inventory",
        inputSchema: {
          type: "object",
          properties: {
            region: {
              type: "string",
              description: "AWS region (default: us-east-1)",
            },
            categories: {
              type: "array",
              items: { type: "string" },
              description: "Optional: specific categories to query (compute, storage, database, networking, security, containers, serverless, all). Default: all",
            },
          },
        },
      },
      {
        name: "get_account_resources",
        description: "Get all major resources for a specific account profile",
        inputSchema: {
          type: "object",
          properties: {
            profile: {
              type: "string",
              description: "AWS profile name",
            },
            region: {
              type: "string",
              description: "AWS region (default: us-east-1)",
            },
          },
          required: ["profile"],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "list_aws_profiles": {
        const profiles = await getAwsProfiles();
        const accountInfo = await getAccountInfo();

        const profileList = profiles.map(profile => ({
          profile,
          accountId: accountInfo[profile]?.accountId || 'N/A',
          role: accountInfo[profile]?.role || 'N/A',
          region: accountInfo[profile]?.region || 'N/A',
        }));

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(profileList, null, 2),
            },
          ],
        };
      }

      case "execute_aws_command": {
        const { profile, command, timeout = 30000 } = args;
        const result = await executeAwsCommand(profile, command, timeout);
        const accountInfo = await getAccountInfo();

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                ...result,
                accountId: accountInfo[profile]?.accountId,
                role: accountInfo[profile]?.role,
              }, null, 2),
            },
          ],
        };
      }

      case "query_all_accounts": {
        const { command, filter_profiles } = args;
        const results = await executeAcrossAllProfiles(command, filter_profiles);

        const summary = {
          total_profiles: results.length,
          successful: results.filter(r => r.success).length,
          failed: results.filter(r => !r.success).length,
          results: results,
        };

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(summary, null, 2),
            },
          ],
        };
      }

      case "get_resource_summary": {
        const { resource_type, region = "us-east-1" } = args;

        const commands = {
          // Storage
          s3: "s3api list-buckets --query 'Buckets[*].[Name,CreationDate]' --output json",
          efs: `efs describe-file-systems --region ${region} --query 'FileSystems[*].[FileSystemId,Name,SizeInBytes.Value]' --output json`,
          fsx: `fsx describe-file-systems --region ${region} --query 'FileSystems[*].[FileSystemId,FileSystemType,StorageCapacity]' --output json`,
          backup: `backup list-backup-vaults --region ${region} --query 'BackupVaultList[*].[BackupVaultName,NumberOfRecoveryPoints]' --output json`,

          // Compute
          ec2: `ec2 describe-instances --region ${region} --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,State.Name,Tags[?Key==\`Name\`].Value|[0]]' --output json`,
          autoscaling: `autoscaling describe-auto-scaling-groups --region ${region} --query 'AutoScalingGroups[*].[AutoScalingGroupName,DesiredCapacity,MinSize,MaxSize]' --output json`,

          // Database
          rds: `rds describe-db-instances --region ${region} --query 'DBInstances[*].[DBInstanceIdentifier,Engine,DBInstanceClass,DBInstanceStatus]' --output json`,
          dynamodb: `dynamodb list-tables --region ${region} --output json`,
          elasticache: `elasticache describe-cache-clusters --region ${region} --query 'CacheClusters[*].[CacheClusterId,CacheNodeType,Engine]' --output json`,
          opensearch: `opensearch list-domain-names --region ${region} --output json`,
          redshift: `redshift describe-clusters --region ${region} --query 'Clusters[*].[ClusterIdentifier,NodeType,NumberOfNodes]' --output json`,

          // Serverless
          lambda: `lambda list-functions --region ${region} --query 'Functions[*].[FunctionName,Runtime,MemorySize,LastModified]' --output json`,
          stepfunctions: `stepfunctions list-state-machines --region ${region} --query 'stateMachines[*].[name,stateMachineArn]' --output json`,
          eventbridge: `events list-rules --region ${region} --query 'Rules[*].[Name,State,ScheduleExpression]' --output json`,
          apigateway: `apigateway get-rest-apis --region ${region} --query 'items[*].[name,id,createdDate]' --output json`,

          // Containers
          ecs: `ecs list-clusters --region ${region} --output json`,
          ecr: `ecr describe-repositories --region ${region} --query 'repositories[*].[repositoryName,repositoryUri,imageScanningConfiguration.scanOnPush]' --output json`,

          // Networking
          vpc: `ec2 describe-vpcs --region ${region} --query 'Vpcs[*].[VpcId,CidrBlock,Tags[?Key==\`Name\`].Value|[0]]' --output json`,
          elb: `elb describe-load-balancers --region ${region} --query 'LoadBalancerDescriptions[*].[LoadBalancerName,Scheme,DNSName]' --output json`,
          alb: `elbv2 describe-load-balancers --region ${region} --query 'LoadBalancers[*].[LoadBalancerName,Type,Scheme,State.Code]' --output json`,
          cloudfront: "cloudfront list-distributions --query 'DistributionList.Items[*].[Id,DomainName,Status]' --output json",
          route53: "route53 list-hosted-zones --query 'HostedZones[*].[Name,Id,ResourceRecordSetCount]' --output json",

          // Security
          "security-hub": `securityhub get-findings --region ${region} --filters '{"SeverityLabel":[{"Value":"CRITICAL","Comparison":"EQUALS"},{"Value":"HIGH","Comparison":"EQUALS"}],"RecordState":[{"Value":"ACTIVE","Comparison":"EQUALS"}]}' --query 'Findings[*].[Title,Severity.Label,Resources[0].Type]' --output json --max-items 50`,
          guardduty: `guardduty list-detectors --region ${region} --output json`,
          kms: `kms list-keys --region ${region} --query 'Keys[*].KeyId' --output json`,
          "secrets-manager": `secretsmanager list-secrets --region ${region} --query 'SecretList[*].[Name,LastChangedDate]' --output json`,
          "ssm-parameters": `ssm describe-parameters --region ${region} --query 'Parameters[*].[Name,Type,LastModifiedDate]' --output json --max-items 50`,
          acm: `acm list-certificates --region ${region} --query 'CertificateSummaryList[*].[DomainName,Status]' --output json`,
          waf: `wafv2 list-web-acls --scope REGIONAL --region ${region} --query 'WebACLs[*].[Name,Id]' --output json`,
          shield: "shield list-protections --query 'Protections[*].[Name,ResourceArn]' --output json",

          // IAM (global)
          "iam-roles": "iam list-roles --query 'Roles[*].[RoleName,CreateDate]' --output json --max-items 100",
          "iam-users": "iam list-users --query 'Users[*].[UserName,CreateDate,PasswordLastUsed]' --output json",
          "iam-policies": "iam list-policies --scope Local --query 'Policies[*].[PolicyName,AttachmentCount]' --output json",

          // Analytics & Data
          kinesis: `kinesis list-streams --region ${region} --output json`,
          glue: `glue get-databases --region ${region} --query 'DatabaseList[*].Name' --output json`,
          athena: `athena list-work-groups --region ${region} --query 'WorkGroups[*].[Name,State]' --output json`,
          emr: `emr list-clusters --region ${region} --active --query 'Clusters[*].[Id,Name,Status.State]' --output json`,

          // ML
          sagemaker: `sagemaker list-endpoints --region ${region} --query 'Endpoints[*].[EndpointName,EndpointStatus]' --output json`,

          // DevOps
          cloudformation: `cloudformation list-stacks --region ${region} --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --query 'StackSummaries[*].[StackName,StackStatus,LastUpdatedTime]' --output json`,
          codepipeline: `codepipeline list-pipelines --region ${region} --query 'pipelines[*].[name,created]' --output json`,
          codebuild: `codebuild list-projects --region ${region} --output json`,

          // Messaging
          sns: `sns list-topics --region ${region} --query 'Topics[*].TopicArn' --output json`,
          sqs: `sqs list-queues --region ${region} --output json`,

          // Monitoring
          "cloudwatch-logs": `logs describe-log-groups --region ${region} --query 'logGroups[*].[logGroupName,storedBytes]' --output json --limit 50`,
        };

        const command = commands[resource_type];
        if (!command) {
          throw new Error(`Unknown resource type: ${resource_type}. Available types: ${Object.keys(commands).join(', ')}`);
        }

        const results = await executeAcrossAllProfiles(command);

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                resource_type,
                region,
                total_profiles: results.length,
                successful: results.filter(r => r.success).length,
                failed: results.filter(r => !r.success).length,
                results,
              }, null, 2),
            },
          ],
        };
      }

      case "get_all_resources": {
        const { region = "us-east-1", categories = ["all"] } = args;

        const resourceCategories = {
          compute: ["ec2", "autoscaling"],
          storage: ["s3", "efs"],
          database: ["rds", "dynamodb", "elasticache"],
          networking: ["vpc", "alb", "route53"],
          security: ["security-hub", "iam-roles", "kms", "secrets-manager"],
          containers: ["ecs", "ecr"],
          serverless: ["lambda", "apigateway", "stepfunctions", "eventbridge"],
          devops: ["cloudformation", "codepipeline"],
          messaging: ["sns", "sqs"],
          analytics: ["kinesis", "glue"],
        };

        // Determine which resource types to query
        let resourcesToQuery = [];
        if (categories.includes("all")) {
          resourcesToQuery = Object.values(resourceCategories).flat();
        } else {
          for (const cat of categories) {
            if (resourceCategories[cat]) {
              resourcesToQuery.push(...resourceCategories[cat]);
            }
          }
        }

        const allCommands = {
          s3: "s3api list-buckets --query 'Buckets[*].[Name,CreationDate]' --output json",
          efs: `efs describe-file-systems --region ${region} --query 'FileSystems[*].[FileSystemId,Name]' --output json`,
          ec2: `ec2 describe-instances --region ${region} --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,State.Name]' --output json`,
          autoscaling: `autoscaling describe-auto-scaling-groups --region ${region} --query 'AutoScalingGroups[*].[AutoScalingGroupName,DesiredCapacity]' --output json`,
          rds: `rds describe-db-instances --region ${region} --query 'DBInstances[*].[DBInstanceIdentifier,Engine,DBInstanceStatus]' --output json`,
          dynamodb: `dynamodb list-tables --region ${region} --output json`,
          elasticache: `elasticache describe-cache-clusters --region ${region} --query 'CacheClusters[*].[CacheClusterId,Engine]' --output json`,
          lambda: `lambda list-functions --region ${region} --query 'Functions[*].[FunctionName,Runtime]' --output json`,
          stepfunctions: `stepfunctions list-state-machines --region ${region} --query 'stateMachines[*].name' --output json`,
          eventbridge: `events list-rules --region ${region} --query 'Rules[*].[Name,State]' --output json`,
          apigateway: `apigateway get-rest-apis --region ${region} --query 'items[*].[name,id]' --output json`,
          ecs: `ecs list-clusters --region ${region} --output json`,
          ecr: `ecr describe-repositories --region ${region} --query 'repositories[*].repositoryName' --output json`,
          vpc: `ec2 describe-vpcs --region ${region} --query 'Vpcs[*].[VpcId,CidrBlock]' --output json`,
          alb: `elbv2 describe-load-balancers --region ${region} --query 'LoadBalancers[*].[LoadBalancerName,Type]' --output json`,
          route53: "route53 list-hosted-zones --query 'HostedZones[*].[Name,Id]' --output json",
          "security-hub": `securityhub get-findings --region ${region} --filters '{"SeverityLabel":[{"Value":"CRITICAL","Comparison":"EQUALS"}],"RecordState":[{"Value":"ACTIVE","Comparison":"EQUALS"}]}' --query 'length(Findings)' --output json`,
          "iam-roles": "iam list-roles --query 'length(Roles)' --output json",
          kms: `kms list-keys --region ${region} --query 'length(Keys)' --output json`,
          "secrets-manager": `secretsmanager list-secrets --region ${region} --query 'length(SecretList)' --output json`,
          cloudformation: `cloudformation list-stacks --region ${region} --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --query 'length(StackSummaries)' --output json`,
          codepipeline: `codepipeline list-pipelines --region ${region} --query 'length(pipelines)' --output json`,
          sns: `sns list-topics --region ${region} --query 'length(Topics)' --output json`,
          sqs: `sqs list-queues --region ${region} --output json`,
          kinesis: `kinesis list-streams --region ${region} --query 'length(StreamNames)' --output json`,
          glue: `glue get-databases --region ${region} --query 'length(DatabaseList)' --output json`,
        };

        // Execute all resource queries in parallel across all profiles
        const resourceResults = {};
        const profiles = await getAwsProfiles();

        await Promise.all(
          resourcesToQuery.map(async (resourceType) => {
            if (allCommands[resourceType]) {
              const results = await executeAcrossAllProfiles(allCommands[resourceType]);
              resourceResults[resourceType] = {
                successful: results.filter(r => r.success).length,
                failed: results.filter(r => !r.success).length,
                results,
              };
            }
          })
        );

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                region,
                categories: categories.includes("all") ? Object.keys(resourceCategories) : categories,
                total_profiles: profiles.length,
                resources: resourceResults,
              }, null, 2),
            },
          ],
        };
      }

      case "get_account_resources": {
        const { profile, region = "us-east-1" } = args;

        const commands = [
          // Storage
          { name: "S3 Buckets", cmd: "s3api list-buckets --query 'Buckets[*].[Name]' --output json" },
          { name: "EFS", cmd: `efs describe-file-systems --region ${region} --query 'FileSystems[*].[FileSystemId,Name]' --output json` },

          // Compute
          { name: "EC2 Instances", cmd: `ec2 describe-instances --region ${region} --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,State.Name]' --output json` },
          { name: "Auto Scaling Groups", cmd: `autoscaling describe-auto-scaling-groups --region ${region} --query 'AutoScalingGroups[*].[AutoScalingGroupName,DesiredCapacity]' --output json` },

          // Database
          { name: "RDS Databases", cmd: `rds describe-db-instances --region ${region} --query 'DBInstances[*].[DBInstanceIdentifier,Engine,DBInstanceStatus]' --output json` },
          { name: "DynamoDB Tables", cmd: `dynamodb list-tables --region ${region} --output json` },
          { name: "ElastiCache", cmd: `elasticache describe-cache-clusters --region ${region} --query 'CacheClusters[*].[CacheClusterId,Engine]' --output json` },

          // Serverless
          { name: "Lambda Functions", cmd: `lambda list-functions --region ${region} --query 'Functions[*].[FunctionName,Runtime]' --output json` },
          { name: "API Gateway", cmd: `apigateway get-rest-apis --region ${region} --query 'items[*].[name,id]' --output json` },
          { name: "Step Functions", cmd: `stepfunctions list-state-machines --region ${region} --query 'stateMachines[*].name' --output json` },
          { name: "EventBridge Rules", cmd: `events list-rules --region ${region} --query 'Rules[*].[Name,State]' --output json` },

          // Containers
          { name: "ECS Clusters", cmd: `ecs list-clusters --region ${region} --output json` },
          { name: "ECR Repositories", cmd: `ecr describe-repositories --region ${region} --query 'repositories[*].repositoryName' --output json` },

          // Networking
          { name: "VPCs", cmd: `ec2 describe-vpcs --region ${region} --query 'Vpcs[*].[VpcId,CidrBlock]' --output json` },
          { name: "Load Balancers", cmd: `elbv2 describe-load-balancers --region ${region} --query 'LoadBalancers[*].[LoadBalancerName,Type]' --output json` },

          // Security
          { name: "Security Hub Findings", cmd: `securityhub get-findings --region ${region} --filters '{"SeverityLabel":[{"Value":"CRITICAL","Comparison":"EQUALS"},{"Value":"HIGH","Comparison":"EQUALS"}],"RecordState":[{"Value":"ACTIVE","Comparison":"EQUALS"}]}' --query 'length(Findings)' --output json` },
          { name: "KMS Keys", cmd: `kms list-keys --region ${region} --query 'length(Keys)' --output json` },
          { name: "Secrets Manager", cmd: `secretsmanager list-secrets --region ${region} --query 'SecretList[*].Name' --output json` },
          { name: "IAM Roles", cmd: "iam list-roles --query 'length(Roles)' --output json" },

          // DevOps
          { name: "CloudFormation Stacks", cmd: `cloudformation list-stacks --region ${region} --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --query 'StackSummaries[*].StackName' --output json` },

          // Messaging
          { name: "SNS Topics", cmd: `sns list-topics --region ${region} --query 'length(Topics)' --output json` },
          { name: "SQS Queues", cmd: `sqs list-queues --region ${region} --output json` },

          // Monitoring
          { name: "CloudWatch Log Groups", cmd: `logs describe-log-groups --region ${region} --query 'length(logGroups)' --output json` },
        ];

        const results = await Promise.all(
          commands.map(async ({ name, cmd }) => {
            const result = await executeAwsCommand(profile, cmd);
            return { name, ...result };
          })
        );

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                profile,
                region,
                resources: results,
              }, null, 2),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("AWS Multi-Account MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
