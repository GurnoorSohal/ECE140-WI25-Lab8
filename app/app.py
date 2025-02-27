import uvicorn
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
import uuid
from typing import Dict
from contextlib import asynccontextmanager

from database import (
    setup_database,
    get_user_by_username,
    get_user_by_id,
    create_session,
    get_session,
    delete_session,
)

# TODO: 1. create your own user
INIT_USERS = {"alice" : "pass123", "bob" : "pass456" , "Gurnoor" : "Hello!"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for managing application startup and shutdown.
    Handles database setup and cleanup in a more structured way.
    """
    # Startup: Setup resources
    try:
        await setup_database(INIT_USERS)  # Make sure setup_database is async
        print("Database setup completed")
        yield
    finally:
        print("Shutdown completed")


# Create FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)


# Static file helpers
def read_html(file_path: str) -> str:
    with open(file_path, "r") as f:
        return f.read()


def get_error_html(username: str) -> str:
    error_html = read_html("./static/error.html")
    return error_html.replace("{username}", username)


@app.get("/")
async def root():
    """Redirect users to /login"""
    # TODO: 2. Implement this route
    return RedirectResponse(url="/login")
    

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Show login if not logged in, or redirect to profile page"""
    # TODO: 3. check if sessionId is in attached cookies and validate it
    # if all valid, redirect to /user/{username}
    # if not, show login page
    session_id = request.cookies.get("sessionId")
    if session_id: 
        session = await get_session(session_id)
        if session:
            return RedirectResponse(url=f"/user/{session['username']}")
    return HTMLResponse(read_html("./static/login.html"))


@app.post("/login")
async def login(request: Request):
    """Validate credentials and create a new session if valid"""
    # TODO: 4. Get username and password from form data
    form_data = await request.form()
    username = form_data.get("username")
    password = form_data.get("password")

    # TODO: 5. Check if username exists and password matches
    user = await get_user_by_username(username)
    if user is None or user["password"] != password:
        return HTMLResponse(get_error_html(username))

    # TODO: 6. Create a new session
    new_session_id = str(uuid.uuid4())
    await create_session(user["id"], new_session_id)

    # TODO: 7. Create response with:
    #   - redirect to /user/{username}
    #   - set cookie with session ID
    #   - return the response
    response = RedirectResponse(url=f"/user/{username}", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="sessionId", value=new_session_id)
    return response


@app.post("/logout")
async def logout(request: Request):
    """Clear session and redirect to login page"""
    # TODO: 8. Create redirect response to /login
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    # TODO: 9. Delete sessionId cookie
    session_id = request.cookies.get("sessionId")
    if session_id:
        await delete_session(session_id)

    # TODO: 10. Return response
    response.delete_cookie("sessionid")
    return response


@app.get("/user/{username}", response_class=HTMLResponse)
async def user_page(username: str, request: Request):
    """Show user profile if authenticated, error if not"""
    # TODO: 11. Get sessionId from cookies
    session_id = request.cookies.get("sessionId")

    # TODO: 12. Check if sessionId exists and is valid
    #   - if not, redirect to /login
    if not session_id:
        return RedirectResponse(url="/login")

    # TODO: 13. Check if session username matches URL username
    #   - if not, return error page using get_error_html with 403 status
    session = await get_session(session_id)
    if not session: 
        return RedirectResponse(url="/login")
    
    user = await get_user_by_id(session["user_id"])
    if not user: 
        return RedirectResponse(url="/login")

    if user["username"] != username:
        return HTMLResponse(get_error_html(username), status_code=status.HTTP_403_FORBIDDEN)


    # TODO: 14. If all valid, show profile page
    profile_html = read_html("./static/profile.html").replace("{username}", username)
    return HTMLResponse(profile_html)

if __name__ == "__main__":
    uvicorn.run("app:app", host="localhost", port=8000, reload=True)
