import { useState } from "react";
import { useRouter } from "next/router";
import { BACKEND_URL } from "../constants/string";


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

const IndexPage = () => {
    const [number, setNumber] = useState<string>(""); // 用于存储输入的座位号
    const [name, setName] = useState<string>(""); // 用于存储输入的用户名
    const router = useRouter();

    const handleChangeNumber = (e: React.ChangeEvent<HTMLInputElement>) => {
        setNumber(e.target.value);
    };

    const handleChangeName = (e: React.ChangeEvent<HTMLInputElement>) => {
        setName(e.target.value);
    };

    const handleLogin = () => {
        // 输入验证：检查座位号是否为 0 到 5 之间的数字，检查用户名是否为空
        if (!number || isNaN(Number(number)) || Number(number) < 0 || Number(number) > 5) {
            alert("Seat number must be a number between 0 and 5.");
            return;
        }
        if (!name.trim()) {
            alert("Seat name cannot be empty.");
            return;
        }

        // 发送请求到后端进行登录
        fetch(`${BACKEND_URL}/api/main/1`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                seatNumber: Number(number),
                seatName: name.trim(),
            }),
        })
            .then((res) => res.json())
            .then((res) => {
                if (Number(res.code) === 0) {
                    // 登录成功，跳转到主页面
                    alert("Login successful!");
                    localStorage.setItem("seatNumber", number);
                    localStorage.setItem("seatName", name.trim());
                    router.push("/room");
                } else {
                    alert("Login failed: " + res.info);
                }
            })
            .catch((err) => alert("Request failed: " + err));
    };

    return (
        <div style={{ padding: "20px", textAlign: "center" }}>
            <h1>Input Your Seat Number and Name</h1>
            <input
                type="number"
                value={number}
                onChange={handleChangeNumber}
                placeholder="Enter seat number (0-5)"
                style={{
                    width: "200px",
                    padding: "8px",
                    fontSize: "16px",
                    marginBottom: "10px",
                }}
            />
            <br />
            <input
                type="text"
                value={name}
                onChange={handleChangeName}
                placeholder="Enter your name"
                style={{
                    width: "200px",
                    padding: "8px",
                    fontSize: "16px",
                    marginBottom: "10px",
                }}
            />
            <br />
            <button
                onClick={handleLogin}
                style={{
                    padding: "10px 20px",
                    fontSize: "16px",
                    cursor: "pointer",
                    marginTop: "10px",
                    backgroundColor: "#007BFF",
                    color: "white",
                    border: "none",
                    borderRadius: "5px",
                }}
            >
                Start VIIV!
            </button>
        </div>
    );
};

export default IndexPage;
