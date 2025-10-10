import json

def lambda_handler(event, context):
    print("===== FULL EVENT =====")
    print(json.dumps(event, indent=2, default=str))
    print("======================")
    
    # Extract from event
    api_path = event.get('apiPath', 'MISSING')
    action_group = event.get('actionGroup', 'MISSING')
    
    print(f"apiPath: {api_path}")
    print(f"actionGroup: {action_group}")
    
    # Return minimal valid response
    response = {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": action_group,
            "apiPath": api_path,
            "httpMethod": "POST",
            "httpStatusCode": 200,
            "responseBody": {
                "application/json": {
                    "body": json.dumps({
                        "success": True,
                        "data": {
                            "total_cost": 123.45,
                            "currency": "USD"
                        }
                    })
                }
            }
        }
    }
    
    print("===== RETURNING =====")
    print(json.dumps(response, indent=2, default=str))
    print("=====================")
    
    return response