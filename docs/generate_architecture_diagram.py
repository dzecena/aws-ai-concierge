#!/usr/bin/env python3
"""
Generate AWS AI Concierge Architecture Diagram
Requires: pip install matplotlib networkx
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

def create_architecture_diagram():
    """Create the AWS AI Concierge architecture diagram."""
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # AWS Colors
    aws_orange = '#FF9900'
    aws_blue = '#232F3E'
    aws_light_blue = '#4B92DB'
    aws_green = '#7AA116'
    aws_purple = '#9D5AAE'
    
    # Title
    ax.text(7, 9.5, 'AWS AI Concierge - Production Architecture', 
            fontsize=16, fontweight='bold', ha='center')
    
    # User
    user_box = FancyBboxPatch((0.5, 7), 2, 1, 
                              boxstyle="round,pad=0.1", 
                              facecolor='lightblue', 
                              edgecolor='black')
    ax.add_patch(user_box)
    ax.text(1.5, 7.5, '👤 User\n"What are my\nAWS costs?"', 
            ha='center', va='center', fontsize=10)
    
    # Bedrock Agent
    bedrock_box = FancyBboxPatch((4, 7), 3, 1, 
                                 boxstyle="round,pad=0.1", 
                                 facecolor=aws_orange, 
                                 edgecolor='black', alpha=0.7)
    ax.add_patch(bedrock_box)
    ax.text(5.5, 7.5, '🤖 Amazon Bedrock\naws-ai-concierge-dev\nClaude 3 Haiku', 
            ha='center', va='center', fontsize=9, color='white', fontweight='bold')
    
    # Lambda Function
    lambda_box = FancyBboxPatch((9, 7), 3, 1, 
                                boxstyle="round,pad=0.1", 
                                facecolor=aws_orange, 
                                edgecolor='black', alpha=0.7)
    ax.add_patch(lambda_box)
    ax.text(10.5, 7.5, '⚡ AWS Lambda\naws-ai-concierge-tools-dev\n512MB Python 3.11', 
            ha='center', va='center', fontsize=9, color='white', fontweight='bold')
    
    # AWS Services Row
    services = [
        ('💰 Cost Explorer', aws_green, 1.5),
        ('🖥️ EC2', aws_orange, 4),
        ('🪣 S3', aws_green, 6.5),
        ('🗄️ RDS', aws_light_blue, 9),
        ('📊 CloudWatch', aws_purple, 11.5)
    ]
    
    for service, color, x_pos in services:
        service_box = FancyBboxPatch((x_pos-0.75, 4.5), 1.5, 1, 
                                     boxstyle="round,pad=0.1", 
                                     facecolor=color, 
                                     edgecolor='black', alpha=0.7)
        ax.add_patch(service_box)
        ax.text(x_pos, 5, service, ha='center', va='center', 
                fontsize=8, color='white', fontweight='bold')
    
    # IAM Roles
    iam_box = FancyBboxPatch((1, 2), 2.5, 1, 
                             boxstyle="round,pad=0.1", 
                             facecolor='#FF6B6B', 
                             edgecolor='black', alpha=0.7)
    ax.add_patch(iam_box)
    ax.text(2.25, 2.5, '🔐 IAM Roles\nRead-only Permissions', 
            ha='center', va='center', fontsize=9, color='white', fontweight='bold')
    
    # CloudWatch Logs
    logs_box = FancyBboxPatch((10, 2), 2.5, 1, 
                              boxstyle="round,pad=0.1", 
                              facecolor=aws_purple, 
                              edgecolor='black', alpha=0.7)
    ax.add_patch(logs_box)
    ax.text(11.25, 2.5, '📝 CloudWatch Logs\nAudit Trail', 
            ha='center', va='center', fontsize=9, color='white', fontweight='bold')
    
    # Arrows - Main Flow
    # User to Bedrock
    arrow1 = ConnectionPatch((2.5, 7.5), (4, 7.5), "data", "data",
                            arrowstyle="->", shrinkA=5, shrinkB=5, 
                            mutation_scale=20, fc="black")
    ax.add_patch(arrow1)
    
    # Bedrock to Lambda
    arrow2 = ConnectionPatch((7, 7.5), (9, 7.5), "data", "data",
                            arrowstyle="->", shrinkA=5, shrinkB=5, 
                            mutation_scale=20, fc="black")
    ax.add_patch(arrow2)
    ax.text(8, 7.8, 'Function-based\nIntegration', ha='center', fontsize=8, 
            style='italic', color='blue')
    
    # Lambda to Services
    for _, _, x_pos in services:
        arrow = ConnectionPatch((10.5, 7), (x_pos, 5.5), "data", "data",
                               arrowstyle="->", shrinkA=5, shrinkB=5, 
                               mutation_scale=15, fc="gray", alpha=0.7)
        ax.add_patch(arrow)
    
    # IAM to Lambda and Bedrock
    iam_arrow1 = ConnectionPatch((2.25, 3), (5.5, 7), "data", "data",
                                arrowstyle="->", shrinkA=5, shrinkB=5, 
                                mutation_scale=15, fc="red", alpha=0.6,
                                linestyle='--')
    ax.add_patch(iam_arrow1)
    
    iam_arrow2 = ConnectionPatch((2.25, 3), (10.5, 7), "data", "data",
                                arrowstyle="->", shrinkA=5, shrinkB=5, 
                                mutation_scale=15, fc="red", alpha=0.6,
                                linestyle='--')
    ax.add_patch(iam_arrow2)
    
    # Lambda to CloudWatch Logs
    logs_arrow = ConnectionPatch((10.5, 7), (11.25, 3), "data", "data",
                                arrowstyle="->", shrinkA=5, shrinkB=5, 
                                mutation_scale=15, fc="purple", alpha=0.6)
    ax.add_patch(logs_arrow)
    
    # Performance and Cost Info
    ax.text(7, 1, 'Production Environment: us-east-1 | Response Time: <15s | Cost: $55-105/month', 
            ha='center', fontsize=10, style='italic', 
            bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('aws_ai_concierge_architecture.png', dpi=300, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    create_architecture_diagram()
    print("Architecture diagram saved as 'aws_ai_concierge_architecture.png'")