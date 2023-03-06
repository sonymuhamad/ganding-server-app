from rest_framework.mixins import RetrieveModelMixin,CreateModelMixin,UpdateModelMixin,DestroyModelMixin,ListModelMixin
from rest_framework.viewsets import GenericViewSet,ReadOnlyModelViewSet


class CreateUpdateDeleteModelViewSet(CreateModelMixin,
                            UpdateModelMixin,
                            DestroyModelMixin,
                            GenericViewSet):
    """
    a viewset that provides default `create()`,`update()`,`destroy()` actions
    """
    pass

class UpdateModelViewSet(UpdateModelMixin,GenericViewSet):
    '''
    a viewset that provides default `update()` actions
    '''
    pass

class CreateModelViewSet(CreateModelMixin,
                            GenericViewSet):
    '''
    a viewset that provides default `create()` actions
    '''
    pass

class GetModelViewSet(ListModelMixin,
                   GenericViewSet):
    '''
    a viewset that provides `list()` by default actions
    '''
    pass

class RetrieveModelViewSet(RetrieveModelMixin,GenericViewSet):
    '''
    a viewset that provides `retrieve()` by default actions
    '''
    pass

class CreateUpdateModelViewSet(CreateModelMixin,
                            UpdateModelMixin,
                            GenericViewSet):
    '''
    a viewset that provides `create(), update()` by default actions
    '''
    pass

class CreateDeleteModelViewSet(CreateModelMixin,
                            DestroyModelMixin,
                            GenericViewSet):
    '''
    a viewset that provides create(), destroy() by default
    '''
    pass


