import json

import overpy

from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.db.models.functions import Distance
from rest_framework import status
from rest_framework.response import Response

from .models import Cafe
from rest_framework.views import APIView

from .serializers import CafeSerializer
from .serializers import OverpassSerialzier


# Create your views here.
class NearbyCafesView(APIView):
    def post(self, request):
        user_location = request.data['user_location']
        response = Response()
        if not user_location:
            response.status_code = 400
            response.data = {
                "message": "No location found"
            }
            return response

        try:
            user_coords = [float(coord) for coord in user_location.split(", ")]
            user_point = Point(user_coords, srid=4326)
            # issue here with dwithin function
            queryset = Cafe.objects.filter(location__dwithin=(user_point, 97)).annotate(
                distance=Distance("location", user_point)).order_by("distance")

            serializer = CafeSerializer(queryset, many=True)

            return Response(serializer.data)
        except:
            response.status_code = 400
            response.data = {
                "message": "Issue with queryset!!",
            }

            return response


class QueryOverpass(APIView):
    def post(self, request, *args, **kwargs):
        try:
            api = overpy.Overpass()

            api_query_top = \
                """
                [out:json][timeout:25];
                (
                """

            api_query_bottom = \
                """
                );
                out body;
                >;
                out skel qt;
                """

            api_middle = ""

            my_serializer = OverpassSerialzier(data=request.data)
            if my_serializer.is_valid():
                bbox = my_serializer.validated_data["bbox"]
                for item in my_serializer.validated_data["query"]:
                    if item == "*":
                        api_middle += f'node["amenity"]{tuple(bbox)};\nway["amenity"]{tuple(bbox)};\nrelation["amenity"]{tuple(bbox)};'
                        break
                    else:
                        api_middle += f'node["amenity"="{item}"]{tuple(bbox)};\nway["amenity"="{item}"]{tuple(bbox)};\nrelation["amenity"="{item}"]{tuple(bbox)};'

                api_query = f"{api_query_top}\n{api_middle}\n{api_query_bottom}\n"
                result = api.query(api_query)

                geojson_result = {
                    "type": "FeatureCollection",
                    "features": [],
                }

                nodes_in_way = []

                for way in result.ways:
                    geojson_feature = None
                    geojson_feature = {
                        "type": "Feature",
                        "id": "",
                        "geometry": "",
                        "properties": {},
                    }
                    poly = []
                    for node in way.nodes:
                        nodes_in_way.append(node.id)
                        poly.append([float(node.lon), float(node.lat)])

                        try:
                            poly = Polygon(poly)
                        except:
                            continue

                        geojson_feature["id"] = f"way_{way.id}"
                        geojson_feature["geometry"] = json.loads(poly.centroid.geojson)
                        geojson_feature["properties"] = {}
                    for k, v in way.tags.items():
                        geojson_feature["properties"][k] = v

                    geojson_result["features"].append(geojson_feature)

                for node in result.nodes:
                    if node.id in nodes_in_way:
                        continue
                    geojson_feature = None
                    geojson_feature = {
                        "type": "Feature",
                        "id": "",
                        "geometry": "",
                        "properties": {},
                    }

                    point = Point([float(node.lon), float(node.lat)]) #
                    geojson_feature["id"] = f"node_{node.id}"
                    geojson_feature["geometry"] = json.loads(point.geojson)
                    geojson_feature["properties"] = {}
                    for k, v in node.tags.items():
                        geojson_feature["properties"][k] = v

                    geojson_result["features"].append(geojson_feature)

                return Response(geojson_result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": f"Error: {e}."}, status=status.HTTP_400_BAD_REQUEST)
