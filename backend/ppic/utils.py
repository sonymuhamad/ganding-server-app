from django.http import QueryDict
import json
from rest_framework import parsers

class MultipartJsonParser(parsers.MultiPartParser):

    def parse(self, stream, media_type=None, parser_context=None):
        result = super().parse(
            stream,
            media_type=media_type,
            parser_context=parser_context
        )
        data = {}

        # for case1 with nested serializers
        # parse each field with json
        
        for key, value in result.data.items():
            
            if type(value) != str:
                data[key] = value
                continue

            keys = key.split('.')
            temp = data
            lenKey = len(keys)

            for i in range(0,len(keys),2):

                if i == lenKey - 1:
                    temp[keys[i]] = value
                else:
                    if keys[i] not in temp:
                        temp[keys[i]] = [{} for _ in range(int(keys[i+1])+1)]
                        temp = temp[keys[i]][int(keys[i+1])]
                    else:
                        lenArr = len(temp[keys[i]])
                        if int(keys[i+1]) > lenArr - 1:
                            temp[keys[i]] = temp[keys[i]] +[{}for _ in range(int(keys[i+1])-(lenArr-1) )] 
                        temp = temp[keys[i]][int(keys[i+1])]
        
        qdict = QueryDict('', mutable=True)
        qdict.update(data)
        # print(qdict,'from utils')

        return parsers.DataAndFiles(qdict, result.files)