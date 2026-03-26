provider "aws" {
  region = "us-east-1" # Change to your preferred region
}

# 1. Create the IoT Thing
resource "aws_iot_thing" "opcua_iotcore" {
  name = "OPCUA_Sensor_Gateway"
}

# 2. Create the Certificate and Private Key
resource "aws_iot_certificate" "cert" {
  active = true
}

# 3. Define the IoT Policy (Allows connecting and publishing)
resource "aws_iot_policy" "pubsub_policy" {
  name = "OPCUA_Full_Access"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["iot:Connect", "iot:Publish", "iot:Receive", "iot:Subscribe"]
        Effect   = "Allow"
        Resource = ["*"]
      }
    ]
  })
}

# 4. Attach Policy to Certificate
resource "aws_iot_policy_attachment" "att" {
  policy = aws_iot_policy.pubsub_policy.name
  target = aws_iot_certificate.cert.arn
}

# 5. Attach Certificate to Thing
resource "aws_iot_thing_principal_attachment" "att" {
  principal = aws_iot_certificate.cert.arn
  thing     = aws_iot_thing.opcua_iotcore.name
}

# 6. Save the Keys to files automatically for Python to use
resource "local_file" "private_key" {
  content  = aws_iot_certificate.cert.private_key
  filename = "${path.module}/private.pem.key"
}

resource "local_file" "cert_pem" {
  content  = aws_iot_certificate.cert.certificate_pem
  filename = "${path.module}/certificate.pem.crt"
}

# Output the Endpoint so you can copy it to your Python script
data "aws_iot_endpoint" "current" {
  endpoint_type = "iot:Data-ATS"
}

output "iot_endpoint" {
  value = data.aws_iot_endpoint.current.endpoint_address
}
