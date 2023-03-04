from rest_framework.serializers import ModelSerializer,Serializer
from rest_framework import serializers
from django.db.models import Q
from .models import *
from manager.shortcuts import invalid

class ConversionUomReadOnlySerializer(ModelSerializer):
    class Meta:
        model = ConversionUom
        fields = '__all__'
        depth = 1

class ConversionUomManagementSerializer(ModelSerializer):

    def validate(self, attrs):
        input = attrs['uom_input']
        output = attrs['uom_output']

        if input == output:
            invalid(" It's forbidden to input conversion data from the same unit")

        uoms = ConversionUom.objects.filter(Q(uom_input = output) & Q(uom_output = input)).first()
        
        if uoms is None:
            return super().validate(attrs)
        invalid(f'{input.name} has become the basis of conversion of {output.name}')

    class Meta:
        model = ConversionUom
        fields = '__all__'

class BasedConversionReadOnlySerializer(ModelSerializer):
    class Meta:
        model = BasedConversionMaterial
        fields = '__all__'
        depth = 2

class BasedConversionManagementSerializer(ModelSerializer):

    def validate(self, attrs):
        input = attrs['material_input']
        unit_input  = input.uom
        output = attrs['material_output']
        unit_output = output.uom
        

        uoms = ConversionUom.objects.filter(Q(uom_input = unit_input) & Q(uom_output = unit_output)).first()

        if uoms is None:
            invalid('Tidak ada data konversi pada unit material tersebut')
        if input == output:
            invalid('Tidak bisa mengkonversi material yang sama')

        return super().validate(attrs)

    class Meta:
        model = BasedConversionMaterial
        fields = '__all__'

class ConversionMaterialReportReadOnlySerializer(ModelSerializer):
    class Meta:
        model = ConversionMaterialReport
        fields = '__all__'
        depth = 2

class ConversionMaterialReportManagementSerializer(ModelSerializer):
    

    def validate(self, attrs):
        '''
        validasi untuk kecukupan material
        '''
        input = attrs['material_input']
        output = attrs['material_output']
        uoms = BasedConversionMaterial.objects.filter(Q(material_input = input) & Q(material_output = output)).first()
        if uoms is None:
            invalid('There is no data conversion material on those material')
        
        used_material = (attrs['quantity_output'] / uoms.quantity_output) * uoms.quantity_input
        stok = input.warehousematerial.quantity
        if used_material > stok:
            invalid(f'Insufficient stock material {input.name}')
        
        return super().validate(attrs)
    
    def create(self, validated_data):
        input = validated_data['material_input']
        output = validated_data['material_output']

        uoms = BasedConversionMaterial.objects.get(material_input = input, material_output=output)
        used_material = (validated_data['quantity_output'] / uoms.quantity_output) * uoms.quantity_input
        
        wh_material_input = input.warehousematerial
        wh_material_input.quantity -= used_material
        wh_material_input.save()

        wh_material_output = output.warehousematerial
        wh_material_output.quantity += validated_data['quantity_output']
        wh_material_output.save()

        validated_data['quantity_input'] = used_material

        return super().create(validated_data)

    class Meta:
        model = ConversionMaterialReport
        fields = '__all__'
        read_only_fields = ['quantity_input']

class MonthlyProductionReportSerializer(Serializer):
    '''
    a serializer for get total quantity production on every month
    '''
    date__year = serializers.IntegerField()
    date__month = serializers.IntegerField()
    total_production = serializers.IntegerField()




