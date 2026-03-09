from flask import Flask, request, jsonify
import time
import uuid

App = Flask(__name__)

Commands = []
DefaultDuration = 10
MaxDuration = 86400

def CleanupCommands():
    Now = time.time()
    Commands[:] = [Item for Item in Commands if Item["ExpireAt"] > Now]

def NormalizeCommand(Command):
    if isinstance(Command, str):
        Action = Command.strip()
        if not Action.startswith("."):
            return None
        return {
            "Action": Action
        }

    if isinstance(Command, dict):
        Action = str(Command.get("Action", "")).strip()
        if not Action.startswith("."):
            return None

        NewCommand = dict(Command)
        NewCommand["Action"] = Action
        return NewCommand

    return None

@App.route("/")
def Home():
    CleanupCommands()
    return jsonify({
        "Status": "running",
        "Routes": ["/set", "/get", "/get_by_player"],
        "CommandsCount": len(Commands),
        "DefaultDuration": DefaultDuration,
        "MaxDuration": MaxDuration,
        "UnlimitedCommandsPerPlayer": True
    })

@App.route("/set", methods=["POST"])
def SetCommand():
    CleanupCommands()

    Data = request.get_json(silent=True) or {}
    PlayerId = str(Data.get("PlayerId", "")).strip()
    Command = Data.get("Command")
    Duration = Data.get("Duration", DefaultDuration)

    if not PlayerId or Command is None:
        return jsonify({
            "Status": "error",
            "Message": "PlayerId and Command are required"
        }), 400

    NormalizedCommand = NormalizeCommand(Command)
    if NormalizedCommand is None:
        return jsonify({
            "Status": "error",
            "Message": 'Only commands with Action starting with "." are allowed'
        }), 400

    try:
        Duration = float(Duration)
    except:
        Duration = DefaultDuration

    if Duration <= 0:
        Duration = DefaultDuration

    if Duration > MaxDuration:
        Duration = MaxDuration

    Now = time.time()

    CommandItem = {
        "Id": str(uuid.uuid4()),
        "PlayerId": PlayerId,
        "Command": NormalizedCommand,
        "CreatedAt": Now,
        "ExpireAt": Now + Duration
    }

    Commands.append(CommandItem)

    return jsonify({
        "Status": "ok",
        "Saved": CommandItem,
        "PlayerId": PlayerId,
        "CommandsCount": len(Commands)
    })

@App.route("/get", methods=["GET"])
def GetCommands():
    CleanupCommands()

    return jsonify({
        "Commands": [
            {
                "Id": Item["Id"],
                "PlayerId": Item["PlayerId"],
                "Command": Item["Command"],
                "CreatedAt": Item["CreatedAt"],
                "ExpireAt": Item["ExpireAt"],
                "TimeLeft": max(0, round(Item["ExpireAt"] - time.time(), 2))
            }
            for Item in Commands
        ],
        "CommandsCount": len(Commands)
    })

@App.route("/get_by_player", methods=["GET"])
def GetCommandsByPlayer():
    CleanupCommands()

    PlayerId = str(request.args.get("PlayerId", "")).strip()

    if not PlayerId:
        return jsonify({
            "Status": "error",
            "Message": "PlayerId is required"
        }), 400

    PlayerCommands = []

    for Item in Commands:
        if Item["PlayerId"] == PlayerId:
            PlayerCommands.append({
                "Id": Item["Id"],
                "PlayerId": Item["PlayerId"],
                "Command": Item["Command"],
                "CreatedAt": Item["CreatedAt"],
                "ExpireAt": Item["ExpireAt"],
                "TimeLeft": max(0, round(Item["ExpireAt"] - time.time(), 2))
            })

    return jsonify({
        "PlayerId": PlayerId,
        "Commands": PlayerCommands,
        "ActiveCount": len(PlayerCommands),
        "UnlimitedCommandsPerPlayer": True
    })

application = App
