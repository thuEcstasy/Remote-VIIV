import React, { useEffect, useState } from "react";

// 长连接地址 (替换为后端 WebSocket 地址)
const WS_URL = "ws://localhost:8080/game";

interface Player {
  id: string; // 玩家唯一标识
  name: string; // 玩家名字
  cards: string[]; // 玩家手牌
  isReady: boolean; // 玩家是否准备
}

const Room: React.FC = () => {
  const [players, setPlayers] = useState<Player[]>([]); // 玩家列表
  const [ws, setWs] = useState<WebSocket | null>(null); // WebSocket 实例
  const [messages, setMessages] = useState<string[]>([]); // 聊天消息记录

  // 初始化 WebSocket 连接
  useEffect(() => {
    const socket = new WebSocket(WS_URL);

    socket.onopen = () => {
      console.log("WebSocket connected");
      socket.send(JSON.stringify({ type: "join", data: { name: "Player1" } })); // 示例加入房间
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
      socket.close();
    };
  }, []);

  // 处理服务器消息
  const handleServerMessage = (message: any) => {
    switch (message.type) {
      case "player_update":
        setPlayers(message.data.players); // 更新玩家列表
        break;
      case "chat":
        setMessages((prev) => [...prev, message.data]); // 更新聊天消息
        break;
      default:
        console.warn("Unknown message type:", message.type);
    }
  };

  // 准备按钮
  const handleReady = () => {
    if (ws) {
      ws.send(JSON.stringify({ type: "ready" }));
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      {/* 游戏画面 */}
      <div style={{ flex: 1, display: "flex", justifyContent: "center", alignItems: "center", position: "relative" }}>
        {Array.from({ length: 6 }).map((_, index) => (
          <div
            key={index}
            style={{
              position: "absolute",
              transform: `rotate(${index * 60}deg) translate(0, -200px) rotate(-${index * 60}deg)`,
              textAlign: "center",
            }}
          >
            {players[index] ? (
              <div>
                <div>{players[index].name}</div>
                <div>{players[index].isReady ? "✅ Ready" : "⏳ Waiting"}</div>
                <div>Cards: {players[index].cards.join(", ")}</div>
              </div>
            ) : (
              <div>Waiting for Player...</div>
            )}
          </div>
        ))}
      </div>

      {/* 控制面板 */}
      <div style={{ display: "flex", justifyContent: "center", padding: "10px", background: "#f0f0f0" }}>
        <button onClick={handleReady} style={{ padding: "10px 20px", fontSize: "16px" }}>
          Ready
        </button>
      </div>

      {/* 聊天框 */}
      <div style={{ padding: "10px", background: "#d9d9d9", overflowY: "scroll", height: "150px" }}>
        {messages.map((msg, idx) => (
          <div key={idx}>{msg}</div>
        ))}
      </div>
    </div>
  );
};

export default Room;
