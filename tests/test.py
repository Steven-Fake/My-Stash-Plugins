from plugins.CosplayOrganizer.graphql import GraphQLUtils

utils = GraphQLUtils(
    {
        "Host": "192.168.31.85",
        "ApiKey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiJzdGV2ZW4iLCJzdWIiOiJBUElLZXkiLCJpYXQiOjE3NjgwNTc4NTB9.fcZOnSUBLVZR4XQFxwWOUpJjPZ7ziucOX160ypSIOkI",
    }
)
utils.format_cosplay_tags()
