import json
import os
import random

import bottle
from bottle import HTTPResponse


@bottle.route("/")
def index():
    return "Your Battlesnake is alive!"


@bottle.post("/ping")
def ping():
    """
    Used by the Battlesnake Engine to make sure your snake is still working.
    """
    return HTTPResponse(status=200)


@bottle.post("/start")
def start():
    """
    Called every time a new Battlesnake game starts and your snake is in it.
    Your response will control how your snake is displayed on the board.
    """
    data = bottle.request.json
    print("START:", json.dumps(data))

    response = {"color": "#2b8020", "headType": "fang", "tailType": "round-bum"}
    return HTTPResponse(
        status=200,
        headers={"Content-Type": "application/json"},
        body=json.dumps(response),
    )


@bottle.post("/move")
def move():
    """
    Called when the Battlesnake Engine needs to know your next move.
    The data parameter will contain information about the board.
    Your response must include your move of up, down, left, or right.
    """
  #  data = bottle.request.json
  #  boardInfo = (json.loads(data))
    boardInfo = bottle.request.json
    
    ## Interpret the board
    head = boardInfo['you']['body'][0]
    tempBoard = boardInfo['board']
    board = interpretBoard(tempBoard)
    board[head['x']][head['y']] = 0 # (our space is "clear", since we need to check for adjacent snake heads but obviously don't care about our own)
    
    ## See which moves are possible (IE do not result in instant death)
    moveOptions = []
    if head['y'] > 0:
        if board[head['x']][head['y']-1] < 100:
            moveOptions.append("up")
    if head['y'] < (boardInfo['board']['height']-1):
        if board[head['x']][head['y']+1] < 100:
            moveOptions.append("down")
    if head['x'] > 0:
        if board[head['x']-1][head['y']] < 100:
            moveOptions.append("left")
    if head['x'] < (boardInfo['board']['width']-1):
        if board[head['x']+1][head['y']] < 100:
            moveOptions.append("right")
    
    move = "down"   # Default move
    tempMax = -999999
    for direction in moveOptions:
        tempValue = checkSquare(direction, board, head, len(boardInfo['you']['body']))
        if (tempValue > tempMax):
            tempMax = tempValue
            move = direction
    
    shout = "I am a python snake at " + str(head['x']) + "," + str(head['y']) + " with " + str(len(moveOptions)) + " options "
    response = {"move": move, "shout": shout}
    return HTTPResponse(
        status=200,
        headers={"Content-Type": "application/json"},
        body=json.dumps(response),
    )

def interpretBoard(boardInfo):
    board = [[-1 for i in range(boardInfo['height'])] for j in range(boardInfo['width'])] 
    for food in boardInfo['food']:
        board[food['x']][food['y']] = 1
    for snake in boardInfo['snakes']:
        snakeln = len(snake['body'])
        for segment in snake['body']:
            board[segment['x']][segment['y']] = 100 + snakeln
            if snakeln == len(snake['body']):
                board[segment['x']][segment['y']] += 100    # (it's a head! double it)
            snakeln -= 1
    return board
    
def checkSquare(direction, board, head, length):
    value = 0   # How good is this move?
    
    target = (0, 0)
    adjacent = []
    # Make a list of the three squares adjacent to this one, so we can navigate to food and anticipate other snakes
    if direction == "up":
        target = (head['x'],head['y']-1)
        adjacent.append((head['x'],head['y']-2))
        adjacent.append((head['x']-1,head['y']-1))
        adjacent.append((head['x']+1,head['y']-1))
    if direction == "down":
        target = (head['x'],head['y']+1)
        adjacent.append((head['x'],head['y']+2))
        adjacent.append((head['x']-1,head['y']+1))
        adjacent.append((head['x']+1,head['y']+1))
    if direction == "left":
        target = (head['x']-1,head['y'])
        adjacent.append((head['x']-2,head['y']))
        adjacent.append((head['x']-1,head['y']+1))
        adjacent.append((head['x']-1,head['y']-1))
    if direction == "right":
        target = (head['x']+1,head['y'])
        adjacent.append((head['x']+2,head['y']))
        adjacent.append((head['x']+1,head['y']+1))
        adjacent.append((head['x']+1,head['y']-1))
    
    # If this square we could move into contains food, that'd good
    if board[target[0]][target[1]] == 1:
        value += 10
    for space in adjacent:
        if (space[0] < 0 or space[1] < 0 or space[0] >= len(board) or space[1] >= len(board[0])):
            # If the adjacent space is off the board, that means the target square is an edge space; which is not preferred as it constrains our options
            value -= 1
        elif (board[space[0]][space[1]] >= 200):
            # If the adjacent space is a head, we're risking a collision
            # If it's longer than us, stay the heck away (but don't rule it out completely; in case this is the only possible move a risk is better than nothing)
            if ((board[space[0]][space[1]] % 100) >= length):
                value -= 100
            # If it's shorter than us, that's good; we might get a kill!
            if (board[space[0]][space[1]] % 100 < length):
                value += 5
        elif (board[space[0]][space[1]] >= 100):
            # If the adjacent space is a tail, that's also restricted movement
            value -= 1
        elif (board[space[0]][space[1]] == 1):
            # (And since we're checking squares adjacent to our target anyway, we might as well look for food there too and plan a move ahead)
            value += 1
    return value

@bottle.post("/end")
def end():
    """
    Called every time a game with your snake in it ends.
    """
    data = bottle.request.json
    print("END:", json.dumps(data))
    return HTTPResponse(status=200)


def main():
    bottle.run(
        application,
        host=os.getenv("IP", "0.0.0.0"),
        port=os.getenv("PORT", "8080"),
        debug=os.getenv("DEBUG", True),
    )


# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

if __name__ == "__main__":
    main()
