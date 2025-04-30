Example of pipeline script for updating service version 

```aiignore
TOKEN_RESPONSE=$(curl -X POST -H "Content-Type: application/json" -d '{"username": "your_username", "password": "your_password"}' http://your-domain.com/api/token/)
TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.token')

# Check token
if [ "$TOKEN" == "null" ]; then
  echo "Failed to obtain token"
  exit 1
fi

# Version updating
UPDATE_RESPONSE=$(curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{"name": "My Service Button", "version": "1.2.3"}' http://your-domain.com/api/update_version/)

echo "Update response: $UPDATE_RESPONSE"
```
###########################

# Api Exmplanation

1. AUTH POST
```aiignore
POST /api/token/
Content-Type: application/x-www-form-urlencoded

username=your_username&password=your_password
```
2. SERVICE VERSION UPDATE POST
```aiignore
POST /api/update_version/
Content-Type: application/json
Authorization: Bearer c1f6a6a2-3d4e-4b6c-9d1a-2f6a6a23d4e4

{
  "name": "My Service Button",
  "version": "1.2.3"
}
```
3. LOGOUT POST
```
POST /api/revoke_token/ HTTP/1.1
Host: your-domain.com
Authorization: Bearer your_token
```