import string
from abc import ABC
from rest_framework import serializers
from cafes.models import Cafe
from django.core.serializers import serialize


class CafeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cafe
        fields = ['id', 'name', 'location']


class OverpassSerialzier(serializers.Serializer):
    query = serializers.CharField(required=True)
    bbox = serializers.CharField(required=True)

    def to_internal_value(self, data):
        STOPWORDS = ('and', 'or', 'amenity', '=', '==')
        internal_rep = {}
        if data.get("query", None):
            query = data["query"]
            mod_query = ""
            for char in query:
                if char in string.punctuation:
                    mod_query += " "
                else:
                    mod_query += char
            mod_query = mod_query.split()
            query = []
            for word in mod_query:
                if word.lower() not in STOPWORDS:
                    query.append(word)

            internal_rep["query"] = query
        if data.get("bbox", None):
            bbox = data["bbox"].split(",")

            shuffled_bbox = [bbox[1], bbox[0], bbox[3], bbox[2]]
            mod_bbox = [float(item) for item in shuffled_bbox]
            internal_rep["bbox"] = mod_bbox

        return internal_rep
