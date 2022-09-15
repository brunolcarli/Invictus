import graphene
import ogame.schema



class Query(ogame.schema.Query, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query)
