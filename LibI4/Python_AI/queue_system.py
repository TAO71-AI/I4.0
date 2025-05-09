# Define variables
Queue: dict[str, dict[int, int]] = {}           # {service, {index, users}}
Times: dict[str, dict[int, list[int]]] = {}     # {service, {index, time in ms}}

def __add_to_queue__(Service: str, Index: int) -> None:
    if (Service not in list(Queue.keys())):
        Queue[Service] = {}
    
    if (Index not in list(Queue[Service].keys())):
        Queue[Service][Index] = 0
    
    if (Service not in list(Times.keys())):
        Times[Service] = {}
    
    if (Index not in list(Times[Service].keys())):
        Times[Service][Index] = []

def AddUserToQueue(Service: str, Index: int) -> None:
    __add_to_queue__(Service, Index)
    Queue[Service][Index] += 1

def RemoveUserFromQueue(Service: str, Index: int) -> None:
    __add_to_queue__(Service, Index)
    Queue[Service][Index] -= 1

    if (Queue[Service][Index] < 0):
        Queue[Service][Index] = 0

def GetUsersFromQueue(Service: str, Index: int) -> int:
    __add_to_queue__(Service, Index)
    return Queue[Service][Index]

def GetIndexFromQueue_Filter(Service: str, Filter: int) -> int:
    idxs = []

    for index in list(Queue[Service].keys()):
        idxs.append(Queue[Service][index])
    
    if (len(idxs) == 0):
        return 0

    if (Filter == 0):
        # Most used index
        return max(idxs)
    elif (Filter == 1):
        # Least used index
        return min(idxs)
    
    raise ValueError("[QUEUE:GetIndexFromQueue_Filter] Invalid filter.")

def AddNewTime(Service: str, Index: int, Ms: int) -> None:
    __add_to_queue__(Service, Index)
    Times[Service][Index].append(Ms)

def GetAllTimes(Service: str, Index: int, Calculate: bool = False) -> list[int] | int:
    __add_to_queue__(Service, Index)
    times = Times[Service][Index]

    if (Calculate):
        if (len(times) == 0):
            return -1

        t = 0

        for ti in times:
            t += ti
        
        times = int(t / len(times))

    return times

def Clear() -> None:
    Queue.clear()
    Times.clear()