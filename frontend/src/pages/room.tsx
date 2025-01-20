import React, { useEffect, useState } from "react";
import internal from "stream";

// 长连接地址 (替换为后端 WebSocket 地址)
const WS_URL = "ws://localhost:8000/ws/game";

interface Player {
  id: number; // 玩家唯一标识
  name: string; // 玩家名字
  cards: string[]; // 玩家手牌
  isReady: boolean; // 玩家是否准备
}
const initialPlayers: Player[] = [
  { id: 0, name: "Player0", cards: [], isReady: false },
  { id: 1, name: "Player1", cards: [], isReady: false },
  { id: 2, name: "Player2", cards: [], isReady: false },
  { id: 3, name: "Player3", cards: [], isReady: false },
  { id: 4, name: "Player4", cards: [], isReady: false },
  { id: 5, name: "Player5", cards: [], isReady: false },
];
const Room: React.FC = () => {
  const [players, setPlayers] = useState<Player[]>(initialPlayers); // 玩家列表
  const [ws, setWs] = useState<WebSocket | null>(null); // WebSocket 实例
  const [messages, setMessages] = useState<string[]>([]); // 聊天消息记录
  const [mySeatNumber, setMySeatNumber] = useState<number>(0);
  const [mySeatName, setMySeatName] = useState<string>("");
  const [ready, setReady] = useState(false); // 控制 ready 状态
  useEffect(() => {
    const seatNumber = localStorage.getItem("seatNumber");
    const seatName = localStorage.getItem("seatName");
    if (seatNumber && seatName) {
      setMySeatNumber(Number(seatNumber));
      setMySeatName(seatName);
    }
  }, []);
  // 初始化 WebSocket 连接
  useEffect(() => {
    if (!ready) {
      return;
    }
    const socket = new WebSocket(WS_URL);

    socket.onopen = () => {
      console.log("WebSocket connected");
      socket.send(JSON.stringify({ type: "join", data: { name: mySeatName, otherSeatNumber: mySeatNumber } })); // 加入房间
    };

    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleServerMessage(message);
    };

    socket.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    socket.onclose = () => {
      console.log("WebSocket disconnected");
    };

    setWs(socket);

    return () => {
      if (!ready) {
        socket.close();
      }
    };
  }, [ready]); // 如果 ready 发生变化，重新创建连接

  // 处理接收到的消息
  const handleServerMessage = (message: any) => {
    console.log("Received message:", message);
    console.log(typeof message);
    // 解析消息
    const { type, data } = message;

    if (type === "join") {
      const { otherSeatNumber, name } = data; // 从消息中获取玩家的 id 和 name

      // 更新玩家列表，如果玩家已存在则更新，否则添加新玩家
      setPlayers((prevPlayers) => {
        const updatedPlayers = prevPlayers.map((player) =>
          player.id === otherSeatNumber
            ? { ...player, name, cards: [], isReady: true } // 如果玩家存在，则更新信息
            : player // 如果玩家不存在，则保持原样
        );
        console.log(`Player ${name} with seatNumber ${otherSeatNumber} has joined the room.`);
        console.log("Updated players:", updatedPlayers);
        return updatedPlayers;
      });
      
    }
  };
  // 准备按钮
  const handleReady = () => {
    setReady(true);
    setPlayers((prev) =>
      prev.map((player, index) => {
        if (index === mySeatNumber) {
          return { ...player, isReady: true, name: mySeatName };
        }
        return player;
      })
    );
    if (ws) {
      // ws.send(JSON.stringify({ type: "ready" }));
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      {/* 游戏画面 */}
      <div style={{ flex: 1, display: "flex", justifyContent: "center", alignItems: "center", position: "relative" }}>
        {Array.from({ length: 6 }).map((_, index) => {
          const isMySeat = index === mySeatNumber;
          let rotationAngle = isMySeat ? 180 : 180 + (index - mySeatNumber + 6) * 60;
          return (
            <div
              key={index}
              style={{
                position: "absolute",
                transform: `rotate(${rotationAngle}deg) translate(0, -200px) rotate(-${rotationAngle}deg)`,
                textAlign: "center",
              }}
            >
              {players[index].isReady ? (
                <div>
                  <div>{players[index].name}</div>
                  <div>✅ Ready</div>
                  <div>Player id: {players[index].id}</div>
                  {index === mySeatNumber ? <div>Cards: {players[index].cards.join(", ")}</div> : null}
                  
                </div>
              ) : (
                  <div>
                    <div>Waiting for Player...</div>
                    <div>Player id: {players[index].id}</div>
                  </div>

              )}
            </div>
          )
        }
        )}
      </div>

      {/* 控制面板 */}
      <div style={{ display: "flex", justifyContent: "center", padding: "10px", background: "#f0f0f0" }}>
        <button onClick={handleReady} style={{ padding: "10px 20px", fontSize: "16px" }}>
          Ready
        </button>
      </div>
    </div>
  );
};

export default Room;
