import os
import json
import ai_config as cfg

class Conv:
    def __init__(self, User: str, Conv: dict[str, list] = {}) -> None:
        # Create the conversation
        self.User: str = User
        self.Conv: dict[str, list] = Conv
    
    def __len__(self) -> int:
        return len(self.Conv)
    
    def __to_dict__(self) -> dict:
        return {"User": self.User, "Conv": self.Conv}
    
    def __append_message_to_conversation__(self, ConvName: str, Role: str, Text: str, Files: list[dict[str, str]]) -> None:
        # Append the message and files to the conversation
        msg = {
            "role": Role,
            "content": []
        }

        # Save the files if allowed in the configuration
        if (cfg.current_data["save_conversation_files"]):
            # Append the files (must be in base64 format!)
            for file in Files:
                msg["content"].append({"type": file["type"], file["type"]: f"data:{file['data']}"})
        
        # Append the text message
        msg["content"].append({"type": "text", "text": Text})

        # Save the conversation
        try:
            self.Conv[ConvName].append(msg)
        except:
            # Conversation doesn't exist, create it
            self.Conv[ConvName] = []
            self.Conv[ConvName].append(msg)

    def GetLengthOfConversation(self, ConvName: str) -> int:
        # Check if the conversation exists
        if (list(self.Conv.keys()).count(ConvName) == 0):
            # It doesn't exist; return 0
            return 0

        # Return the length of the conversation
        return len(self.Conv[ConvName])

    def AppendMessageToConversation_User(self, ConvName: str, Text: str, Files: list[dict[str, str]]) -> None:
        self.__append_message_to_conversation__(ConvName, "user", Text, Files)

    def AppendMessageToConversation_Assistant(self, ConvName: str, Text: str, Files: list[dict[str, str]]) -> None:
        self.__append_message_to_conversation__(ConvName, "assistant", Text, Files)
    
    def GetFromID(self, ConvName: str, MessageID: int) -> dict[str, list[dict[str, str]] | str]:
        # Check if the conversation exists
        if (list(self.Conv.keys()).count(ConvName) == 0):
            # It doesn't exist; raise error
            raise Exception("Conversation doesn't exist.")

        # Check if the message exists
        if (len(self.Conv[ConvName]) <= MessageID):
            # Invalid ID, raise error
            raise ValueError("Invalid MessageID (len(conv) <= MessageID).")
        
        # Get the message from the specified ID
        return self.Conv[ConvName][MessageID]
    
    def GetFromID_Old(self, ConvName: str, MessageID: int) -> dict[str, str]:
        # Get the message
        msg = self.GetFromID(ConvName, MessageID)

        # Get the role and content
        role = msg["role"]
        content = msg["content"]
        text = ""

        # For every message in the content
        for contMsg in content:
            # Check if the type is text
            if (contMsg["type"] != "text"):
                # It isn't; continue
                continue
            
            # It is; add to the text
            # Check if the text is empty
            if (len(text) > 0):
                # It's not empty; add a new line
                text += "\n"
            
            # Add the text
            text += contMsg["text"]
        
        # Return the text of the message (this conversation type doesn't support files)
        return {"role": role, "content": text}

    def DeleteMessageFromConversation(self, ConvName: str, MessageID: int) -> None:
        # Delete the message
        self.Conv[ConvName].remove(self.GetFromID(ConvName, MessageID))
        
    def DeleteConversation(self, ConvName: str) -> None:
        try:
            # Try to delete the conversation
            del self.Conv[ConvName]
        except:
            # Error deleting, set to empty
            self.Conv[ConvName] = {}

Conversations: list[Conv] = []

def Init() -> None:
    # Check the files and directories
    if (not os.path.exists("Conversations/")):
        os.mkdir("Conversations/")

def GetConversationFromUser(User: str, CreateIfError: bool) -> Conv:
    # For each conversation
    for conv in Conversations:
        # Check if the user is the same
        if (conv.User == User):
            # Return the conversation
            return conv
    
    if (CreateIfError):
        # Create the conversation
        return Conv(User)
    
    # User doesn't exist, return error
    raise Exception("User not found in conversations.")

def CheckIfTheConversationExists(User: str) -> bool:
    try:
        # Try to get the conversation
        GetConversationFromUser(User)
        return True
    except:
        # Error getting the conversation, doesn't exists
        return False

def DeleteConversationOfUser(User: str) -> None:
    # Get the conversation of the user
    conv = GetConversationFromUser(User)

    # Delete from the list
    Conversations.remove(conv)

    # Delete the conversation directory
    try:
        os.remove(f"Conversations/{conv.User}.json")
    except Exception as ex:
        print(f"Error deleting the conversation of the user {conv.User}: {ex}")

def CreateConversation(User: str) -> Conv:
    # Check if the conversation exists
    if (CheckIfTheConversationExists(User)):
        # Return the conversation
        return GetConversationFromUser(User)

    # Create the conversation
    conv = Conv(User)

    # Append the conversation to the list
    Conversations.append(conv)

    # Return the conversation
    return conv

def CreateFromOldConversation(User: str, Conversation: dict[str, list[dict[str, str]]]) -> Conv:
    # Create the conversation
    conv = Conv(User)

    # For each conversation
    for conversation in list(Conversation.keys()):
        # For each message
        for message in Conversation[conversation]:
            # Get the role and content
            role = message["role"]
            content = message["content"]

            # Check the role
            if (role == "user"):
                conv.AppendMessageToConversation_User(conversation, content, [])
            elif (role == "assistant"):
                conv.AppendMessageToConversation_Assistant(conversation, content, [])
            else:
                # Invalid role, ignore
                print("WARNING! Invalid role when importing conversation.")
    
    # Return the conversation
    return conv

def SaveConversations() -> None:
    # For each conversation
    for conv in Conversations:
        # Save the conversation
        SaveConversation(conv)

def SaveConversation(Conversation: Conv) -> None:
    # Init
    Init()

    # Get the user
    user = Conversation.User

    # Save the conversation
    with open(f"Conversations/{user if (len(user) > 0) else 'none'}.json", "w+") as f:
        f.write(json.dumps(Conversation.__to_dict__()))

def LoadConversations() -> list[Conv]:
    # Init
    Init()
    convs = []

    # For each file in the "Conversations/" directory
    for file in os.listdir("Conversations/"):
        # Get the user from the file name
        user = file[:-5]  # File name - ".json"

        # Load the conversation and append to the list
        convs.append(LoadConversation(user if (user != "none") else ""))
    
    # Return the list of conversations
    return convs

def LoadConversation(User: str) -> Conv:
    # Init
    Init()

    # Check if the conversation exists
    if (not os.path.exists(f"Conversations/{User if (len(User) > 0) else 'none'}.json")):
        # The conversation doesn't exist, return error
        raise Exception(f"Conversation of the user '{User}' doesn't exist.")

    # Load the conversation
    with open(f"Conversations/{User if len(User) > 0 else 'none'}.json", "r") as f:
        conversation = json.loads(f.read())
        f.close()
    
    try:
        # Try to load the conversation normally
        conversation = Conv(conversation["User"], conversation["Conv"])
    except:
        # Error loading the conversation, try using the old method
        print("Error loading conversation... Trying using the old conversation method.")
        conversation = CreateFromOldConversation(User, conversation)

    # Return the conversation
    return conversation

# Load the conversations
Conversations = LoadConversations()