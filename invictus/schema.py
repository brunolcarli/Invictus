import graphene
import ogame.schema
import graphql_jwt


class Query(ogame.schema.Query, graphene.ObjectType):
    pass


class Mutation(graphene.ObjectType, ogame.schema.Mutation):
    log_in = graphql_jwt.ObtainJSONWebToken.Field()
    validate_user_token = graphql_jwt.Verify.Field()
    refresh_user_token = graphql_jwt.Refresh.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
