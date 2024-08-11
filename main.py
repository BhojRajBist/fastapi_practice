# from fastapi import Depends, HTTPException, status,FastAPI
# from models import Base 
# from database import engine ,SessionLocal
# from pydantic import BaseModel
# import models

# app = FastAPI()

# db = SessionLocal()
# # @app.on_event("startup")
# # def startup_event():
# #     Base.metadata.create_all(bind=engine)

# # @app.get("/")
# # async def root():
# #     return {"message": "Hello World"}

# # @app.get("/name/{name_id}")
# # async def name(name_id: int):
# #     return {"message": f"Hello {name_id}"}


# class OurBaseModel(BaseModel):
#     class Config:
#         orm_mode= True


# class Person(OurBaseModel):
#     id : int
#     firstn : str
#     lastn : str
#     isMale : bool


# @app.get("/",response_model=list[Person])
# def get_AllPersons():
#     get_AllPersons= db.query(models.Person).all()
#     return get_AllPersons


# @app.post("/addPerson",response_model=Person)
# def add_Person(person:Person):
#     print(person)
#     newPerson = models.Person(
#         id = person.id,
#         firstn = person.firstn,
#         lastn = person.lastn,
#         isMale = person.isMale
#     )

#     find_person = db.query(models.Person).filter(models.Person.id == person.id).first()

#     if find_person is not None:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Person with this ID already exists")
#     db.add(newPerson)
#     db.commit()

#     return newPerson
import rasterio
import numpy as np
from rasterio.features import shapes
from rasterio.warp import transform_geom
from typing import List, Dict
from mapbox_vector_tile import encode
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import Response
import os
import json  # Import json for debugging
import io  # Import io for BytesIO

app = FastAPI()

def classify_flood_extent(file_path: str) -> List[Dict]:
    with rasterio.open(file_path) as src:
        raster = src.read(1)
        transform = src.transform

        # Mask out pixels below or equal to 0 meters
        raster = np.where(raster <= 0, np.nan, raster)

        # Classification thresholds
        shallow_threshold = 0.5
        moderate_threshold = 1.5
        deep_threshold = 3.0

        # Create an empty mask with the same shape as the raster
        classification = np.zeros_like(raster, dtype=np.uint8)

        # Assign classification values based on flood depth thresholds
        classification[raster > deep_threshold] = 3
        classification[(raster > moderate_threshold) & (raster <= deep_threshold)] = 2
        classification[(raster > shallow_threshold) & (raster <= moderate_threshold)] = 1
        classification[np.isnan(raster)] = 0

        # Define classification mapping
        class_mapping = {
            1: 'shallow',
            2: 'moderate',
            3: 'deep'
        }

        # Extract polygons for each class
        geometries = []
        for class_value, class_name in class_mapping.items():
            mask = classification == class_value
            shapes_generator = shapes(mask.astype(np.int16), mask=mask, transform=transform)
            
            for geom, val in shapes_generator:
                geom_transformed = transform_geom(src.crs, 'EPSG:4326', geom)
                geometries.append({
                    'type': 'Feature',
                    'geometry': geom_transformed,
                    'properties': {
                        'classification': class_name
                    }
                })

    return geometries

def convert_to_mvt(geometries: List[Dict]) -> bytes:
    """Convert classified flood geometries to Mapbox Vector Tile (MVT) format."""
    
    # Prepare layer data
    layer_name = "flood_zones"  # Name of the layer
    layer_data = {
        layer_name: {
            "name": layer_name,  # Add the 'name' key here
            "features": []  # Initialize the features list
        }
    }
    
    # Populate features
    for feature in geometries:
        geom = feature['geometry']
        properties = feature['properties']
        
        # Append the feature to the layer
        layer_data[layer_name]['features'].append({
            "geometry": geom,  # Ensure this is a valid GeoJSON geometry
            "properties": properties
        })

    # Print the layer data for debugging
    print("Layer Data:", json.dumps(layer_data, indent=2))
    
    # Encode the features into MVT
    buffer = io.BytesIO()
    encode(layer_data, buffer)
    buffer.seek(0)

    return buffer.getvalue()

@app.post("/classify_flood/")
async def classify_flood(file: UploadFile = File(...)):
    """Classify the uploaded COG raster file into flood zones and return MVT."""
    # Save the uploaded file temporarily
    temp_file_path = "temp_cog.tiff"
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await file.read())

    # Process the flood raster and convert to GeoJSON
    geometries = classify_flood_extent(temp_file_path)

    # Convert to MVT
    mvt_data = convert_to_mvt(geometries)

    # Clean up the temporary file
    os.remove(temp_file_path)

    # Return the MVT data as a response
    return Response(content=mvt_data, media_type="application/vnd.mapbox-vector-tile")
