import WebSocket from "ws";
import { existsSync, promises as fs } from "fs";
import { exec } from "child_process";
import { Config } from "./Config"
import { InternetSearchManager, Service, ServiceManager } from "./Service";

var ServersTasks: Map<number, Service[]> = new Map();
var Connected: string = "";
var ClientSocket: WebSocket | null = null;
export var OnConnectingToServerAction: ((Server: string) => void) | null = null;
export var OnConnectedToServerAction: ((Server: string) => void) | null = null;
export var OnDisconnectedFromServerAction: (() => void) | null = null;
export var OnSendDataAction: ((Data: Buffer) => void) | null = null;
export var OnReceiveDataAction: ((Data: Buffer) => void) | null = null;
export var Conf: Config = new Config();

export function GetTasks(): Map<number, Service[]>
{
    return new Map(ServersTasks);
}

export async function Connect(Server: string): Promise<void>
{
    await Disconnect();

    OnConnectingToServerAction?.(Server);
    ClientSocket = new WebSocket(`ws://${Server}:8060`);
    let time = 0;

    while (ClientSocket.readyState != WebSocket.OPEN)
    {
        if (time > 50)
        {
            throw new Error("Server not responding.");
        }

        await new Promise(resolve => setTimeout(resolve, 100));
        time++;
    }

    Connected = Server;
    OnConnectedToServerAction?.(Server);
}

export async function ConnectByID(Server: number): Promise<void>
{
    if (Server < 0 || Server >= Conf.Servers.length)
    {
        throw new Error("Invalid server ID.");
    }

    await Connect(Conf.Servers[Server]);
}

export async function Disconnect(): Promise<void>
{
    if (ClientSocket)
    {
        try
        {
            ClientSocket.close();
        }
        finally
        {
            ClientSocket = null;
            OnDisconnectedFromServerAction?.();
        }
    }

    Connected = "";
}

export async function ReceiveFromServer(): Promise<Buffer>
{
    return new Promise((resolve, reject) =>
    {
        if (!ClientSocket)
        {
            return reject("No ClientSocket available.");
        }

        let data: Buffer[] = [];

        ClientSocket.on("message", (message: WebSocket.MessageEvent) =>
        {
            if (message instanceof Buffer)
            {
                data.push(message);
            }
            else if (typeof message == "string")
            {
                data.push(Buffer.from(message));
            }

            if (ClientSocket?.readyState == WebSocket.CLOSED)
            {
                resolve(Buffer.concat(data));
            }
        });
    });
}

export async function SendAndReceive(Data: Buffer): Promise<Buffer>
{
    if (!IsConnected())
    {
        throw new Error("Connect to a server first.");
    }

    ClientSocket?.send(Data, { binary: true });
    OnSendDataAction?.(Data);

    let received = await ReceiveFromServer();
    OnReceiveDataAction?.(received);

    return received;
}

export async function GetServicesFromServer(): Promise<Service[]>
{
    if (!IsConnected())
    {
        throw new Error("Connect to a server first.");
    }

    const requestData = {
        Service: "get_all_services",
        Prompt: "",
        Files: {}
    }
    const received = await SendAndReceive(Buffer.from(JSON.stringify(requestData)));
    const receivedData = JSON.parse(received.toString());
    const jsonData = JSON.parse(receivedData.response as string);
    const services: Service[] = [];

    for (const service of Object.keys(jsonData))
    {
        if (!services.includes(ServiceManager.FromString(service)))
        {
            services.push(ServiceManager.FromString(service));
        }
    }

    return services;
}

export async function FindFirstServer(ServiceToExecute: Service, DeleteData: boolean = false): Promise<number>
{
    if (DeleteData || ServersTasks.size == 0)
    {
        ServersTasks.clear();
        let serverToReturn = -1;

        for (const server of Conf.Servers)
        {
            try
            {
                await Connect(server);

                const services = await GetServicesFromServer();
                ServersTasks.set(Conf.Servers.indexOf(server), services);

                if (services.includes(ServiceToExecute) && serverToReturn < 0)
                {
                    serverToReturn = Conf.Servers.indexOf(server);
                    break;
                }
            }
            catch
            {
                
            }
        }

        return serverToReturn;
    }
    else
    {
        for (const [serverID, services] of ServersTasks.entries())
        {
            if (services.includes(ServiceToExecute))
            {
                return serverID;
            }
        }

        return -1;
    }
}

export function IsConnected(): boolean
{
    return ClientSocket != null && ClientSocket.readyState == WebSocket.OPEN;
}

export async function *SendAndWaitForStreaming(Data: string): AsyncIterableIterator<{ [key: string]: any }>
{
    let responseBytes = await SendAndReceive(Buffer.from(Data, "utf-8"));
    let responseStr = responseBytes.toString();
    let response: { [key: string]: any } = JSON.parse(responseStr);

    while (!response["ended"])
    {
        yield response;

        responseBytes = await ReceiveFromServer();
        responseStr = responseBytes.toString();
        response = JSON.parse(responseStr);
    }

    yield response;
    return;
}

export async function *ExecuteCommand(Service: string, Prompt: string = "", Index: number = -1): AsyncIterableIterator<{ [key: string]: any }>
{
    const jsonData = JSON.stringify({
        APIKey: Conf.ServerAPIKey,
        Files: {},
        Service: Service,
        Prompt: Prompt,
        Conversation: Conf.Chatbot_Conversation,
        Index: Index
    });

    return SendAndWaitForStreaming(jsonData);
}

export async function *AutoGetResponseFromServer(Prompt: string, ServerService: Service, Index: number = -1, ForceNoConnect: boolean = false): AsyncIterableIterator<{ [key: string]: any }>
{
    if (!ForceNoConnect)
    {
        const server = await FindFirstServer(ServerService);
        await ConnectByID(server);
    }
    else if (!IsConnected())
    {
        throw new Error("Please connect to a server first or set `ForceNoConnect` to false.");
    }

    if (ServerService == Service.DepthEstimation || ServerService == Service.ImageToImage || ServerService == Service.ImageToText || ServerService == Service.NSFWFilterImage || ServerService == Service.ObjectDetection || ServerService == Service.RVC || ServerService == Service.UVR || ServerService == Service.SpeechToText)
    {
        if (!existsSync(Prompt))
        {
            throw new Error("File not found.");
        }

        try
        {
            try
            {
                const filests: string[] = JSON.parse(Prompt.trimStart().trimEnd());

                Prompt = "";

                for (const file of filests)
                {
                    const fID = await SendFileToServer(file);
                    Prompt += fID.toString() + " ";
                }

                Prompt = Prompt.trimStart().trimEnd();
            }
            catch (ex)
            {
                let re = true;

                if (ex instanceof SyntaxError)
                {
                    re = false;

                    try
                    {
                        const fID = await SendFileToServer(Prompt);
                        Prompt = fID.toString();
                    }
                    catch
                    {
                        re = true;
                    }
                }

                if (re)
                {
                    throw ex;
                }
            }
        }
        catch (ex)
        {
            throw new Error("Error sending file/s. Probably the server doesn't accept files?");
        }
    }

    let files: { [key: string]: any }[] = [];

    switch (ServerService)
    {
        case Service.ImageGeneration:
            let prompt;
            let nPrompt;

            if (Prompt.includes(" [NEGATIVE] "))
            {
                prompt = Prompt.substring(0, Prompt.indexOf(" [NEGATIVE] "));
                nPrompt = Prompt.substring(Prompt.indexOf(" [NEGATIVE] ") + 12);
            }
            else
            {
                prompt = Prompt;
                nPrompt = "";
            }

            Prompt = JSON.stringify({
                prompt: prompt,
                negative_prompt: nPrompt,
                width: Conf.Text2Image_Width,
                height: Conf.Text2Image_Height,
                guidance: Conf.Text2Image_GuidanceScale,
                steps: Conf.Text2Image_Steps
            });
            break;
        case Service.ImageToImage:
            Prompt.split(" ").forEach(file =>
            {
                files.push({
                    type: "image",
                    name: file
                });
            });

            Prompt = "";
            break;
        case Service.ImageToText:
            Prompt.split(" ").forEach(file =>
            {
                files.push({
                    type: "image",
                    name: file
                });
            });

            Prompt = "";
            break;
        case Service.TTS:
            Prompt = JSON.stringify({
                voice: Conf.TTS_Voice,
                language: Conf.TTS_Language,
                pitch: Conf.TTS_Pitch,
                speed: Conf.TTS_Speed,
                text: Prompt
            });
            break;
        case Service.RVC:
            Prompt.split(" ").forEach(file =>
            {
                files.push({
                    type: "audio",
                    name: file
                });
            });

            Prompt = JSON.stringify({
                model: Conf.RVC_Model,
                filter_radius: Conf.RVC_FilterRadius,
                f0_up_key: Conf.RVC_F0,
                protect: Conf.RVC_Protect
            });
            break;
        case Service.UVR:
            Prompt.split(" ").forEach(file =>
            {
                files.push({
                    type: "audio",
                    name: file
                });
            });

            Prompt = JSON.stringify({
                agg: Conf.UVR_Agg
            });
            break;
        case Service.DepthEstimation:
            Prompt.split(" ").forEach(file =>
            {
                files.push({
                    type: "image",
                    name: file
                });
            });
    
            Prompt = "";
            break;
        case Service.ObjectDetection:
            Prompt.split(" ").forEach(file =>
            {
                files.push({
                    type: "image",
                    name: file
                });
            });
        
            Prompt = "";
            break;
        case Service.NSFWFilterImage:
            Prompt.split(" ").forEach(file =>
            {
                files.push({
                    type: "image",
                    name: file
                });
            });
            
            Prompt = "";
            break;
        case Service.SpeechToText:
            Prompt.split(" ").forEach(file =>
            {
                files.push({
                    type: "audio",
                    name: file
                });
            });
            
            Prompt = "";
            break;
    }

    Prompt = JSON.stringify({
        Service: ServiceManager.ToString(ServerService),
        Prompt: Prompt,
        Files: files,
        APIKey: Conf.ServerAPIKey,
        Conversation: Conf.Chatbot_Conversation,
        AIArgs: Conf.Chatbot_AIArgs,
        SystemPrompts: Conf.Chatbot_ExtraSystemPrompts,
        UseDefaultSystemPrompts: Conf.Chatbot_AllowServerSystemPrompts,
        Internet: InternetSearchManager.ToString(Conf.InternetOptions),
        Index: Index
    });

    return await SendAndWaitForStreaming(Prompt);
}

export async function GetQueueForService(QueueService: Service, Index: number = -1): Promise<[number, number]>
{
    const res = ExecuteCommand("get_queue", ServiceManager.ToString(QueueService), Index);

    for await (const response of res)
    {
        if (!response["ended"])
        {
            throw new Error("Queue error: Invalid ended arg.");
        }

        const queue = JSON.parse(response["response"]);
        return [queue["users"], queue["time"]];
    }

    throw new Error("Queue error: Error getting queue.");
}

export async function DeleteConversation(Conversation: string | null = null): Promise<void>
{
    if (Conversation == null)
    {
        Conversation = Conf.Chatbot_Conversation;
    }

    const res = ExecuteCommand("clear_conversation");

    for await (const response of res)
    {
        if (!response["ended"])
        {
            throw new Error("Delete conversation error: Invalid ended arg.");
        }

        const result = response["response"].toLowerCase().trimStart().trimEnd();

        if (result != "conversation deleted.")
        {
            throw new Error("Error deleting the conversation. Got `" + result + "`; `conversation deleted.` expected.");
        }

        return;
    }

    throw new Error("Delete conversation error: Error getting queue.");
}

export async function GetTOS(): Promise<string>
{
    const res = ExecuteCommand("get_tos");

    for await (const response of res)
    {
        if (!response["ended"])
        {
            throw new Error("Error getting TOS: Invalid ended arg.");
        }

        let tResponse: string = response["response"];
        tResponse = tResponse.trimStart().trimEnd();

        if (tResponse.length == 0)
        {
            return "No TOS.";
        }

        return tResponse;
    }

    throw new Error("Error getting TOS: No response from server.");
}

export async function SendFileToServer(FilePath: string): Promise<number>
{
    if (!existsSync(FilePath))
    {
        throw new Error("File doesn't exists.");
    }

    if (!IsConnected())
    {
        throw new Error("Connect to a server first.");
    }

    const fileBytes = await fs.readFile(FilePath);
    const chunkSize = 4096;
    const totalChunks = Math.ceil(fileBytes.length / chunkSize);
    const maxTime = 50;
    let time = 0;
    const client = new WebSocket(`ws://${Connected}:8061`);

    while (client.readyState != WebSocket.OPEN)
    {
        if (time > maxTime)
        {
            throw new Error("Could not connect to Rec Files server.");
        }

        await new Promise(resolve => setTimeout(resolve, 100));
        time++;
    }

    try
    {
        for (let i = 0; i < totalChunks; i++)
        {
            const offset = i * chunkSize;
            const length = Math.min(chunkSize, fileBytes.length - offset);
            const chunk = Buffer.alloc(length);

            fileBytes.copy(chunk, 0, offset, offset + length);

            await client.send(chunk, { binary: true });

            if (i == totalChunks - 1)
            {
                break;
            }
        }

        await client.send(Buffer.from("<end>"), { binary: true })
    }
    catch
    {
        await client.close();
        throw new Error("Bytes limit error.");
    }

    return new Promise<number>((resolve, reject) =>
    {
        const rbuffer = Buffer.alloc(64);
    
        client.on("message", (data: WebSocket.Data) =>
        {
            let bufferData: Buffer;

            if (Buffer.isBuffer(data))
            {
                bufferData = data;
            }
            else if (data instanceof ArrayBuffer)
            {
                bufferData = Buffer.from(data);
            }
            else
            {
                reject(new Error("Received data is neither Buffer nor ArrayBuffer."));
                return;
            }

            bufferData.copy(rbuffer, 0, 0, Math.min(bufferData.length, rbuffer.length));

            client.close();

            const fileID = parseInt(rbuffer.toString("utf-8").trim(), 10);
            resolve(fileID);
        });
    });
}

export function OpenFile(Path: string): void | HTMLImageElement | HTMLAudioElement
{
    if (!existsSync(Path))
    {
        throw new Error("File doesn't exists.");
    }

    const isBrowser = typeof window != "undefined";
    const ext = Path.split(".").pop()?.toLowerCase() || "";
    let programName;
    let programArgs = "";
    let type;

    if (["png", "jpeg", "jpg"].includes(ext))
    {
        programName = Conf.DefaultImagesProgram;
        type = "image";
    }
    else if (["wav", "mp3", "flac"].includes(ext))
    {
        programName = Conf.DefaultAudiosProgram;
        type = "audio";
    }
    else
    {
        throw new Error("Invalid/unknown file type.");
    }

    if (isBrowser)
    {
        if (type == "image")
        {
            const imageElement = document.createElement("img");
            fetch(Path).then(response => response.arrayBuffer()).then(arrayBuffer =>
            {
                const blob = new Blob([arrayBuffer]);
                imageElement.src = URL.createObjectURL(blob);
            });
        }
        else if (type == "audio")
        {
            const audioElement = document.createElement("audio");
            fetch(Path).then(response => response.arrayBuffer()).then(arrayBuffer =>
            {
                const blob = new Blob([arrayBuffer]);
                audioElement.src = URL.createObjectURL(blob);
            });
        }
    }
    else
    {
        if (programName.trim().length == 0)
        {
            programName = Path;
        }
        else
        {
            programArgs = Path;
        }

        exec(`${programName} ${programArgs}`, (error, stdout, stderr) => {});
    }
}