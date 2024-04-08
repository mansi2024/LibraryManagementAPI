from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
from typing import List, Optional
import urllib.parse

# Encode username and password
username = urllib.parse.quote_plus("simu")
password = urllib.parse.quote_plus("hello@2323")

# Define MongoDB connection with encoded username and password
client = MongoClient(f"mongodb+srv://{username}:{password}@cluster0.ajsfxoc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["library"]
students_collection = db["students"]

# FastAPI instance
app = FastAPI()

# Pydantic models
class Address(BaseModel):
    city: str
    country: str

class Student(BaseModel):
    name: str
    age: int
    address: Address

class StudentOut(Student):
    id: str

class StudentUpdate(BaseModel):
    name: str = None
    age: int = None
    address: Address = None

# Routes
@app.post("/students", response_model=StudentOut, status_code=201)
async def create_student(student: Student):
    result = students_collection.insert_one(student.model_dump())
    created_student = students_collection.find_one({"_id": result.inserted_id})
    return {**created_student, "id": str(created_student["_id"])}

@app.get("/students", response_model=List[StudentOut])
async def get_students(country: Optional[str] = Query(None), age: Optional[int] = Query(None)):
    query = {}
    if country:
        query["address.country"] = country
    if age:
        query["age"] = {"$gte": age}
    students = students_collection.find(query)
    return [{**student, "id": str(student["_id"])} for student in students]

@app.get("/students/{id}", response_model=StudentOut)
async def get_student(id: str):
    student = students_collection.find_one({"_id": ObjectId(id)})
    if student:
        return {**student, "id": str(student["_id"])}
    else:
        raise HTTPException(status_code=404, detail="Student not found")

@app.patch("/students/{id}", response_model=Student)
async def update_student(id: str, student_update: StudentUpdate):
    # Retrieve the existing student from the database
    existing_student = students_collection.find_one({"_id": ObjectId(id)})
    if existing_student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    # Update the student with the fields provided in the request body
    update_fields = {}
    for field_name, field_value in student_update.model_dump().items():
        if field_value is not None:
            update_fields[field_name] = field_value
    
    # Update the student in the database
    students_collection.update_one({"_id": ObjectId(id)}, {"$set": update_fields})
    
    # Return the updated student
    updated_student = students_collection.find_one({"_id": ObjectId(id)})
   
   



@app.delete("/students/{id}", response_model=dict)
async def delete_student(id: str):
    deleted_student = students_collection.delete_one({"_id": ObjectId(id)})
    if deleted_student.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Student deleted successfully"}
