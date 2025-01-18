import { useState } from "react";
import { useRouter } from "next/router";

const IndexPage = () => {
    const [number, setNumber] = useState<string>(""); // 用于存储输入的数字
    const router = useRouter();

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setNumber(e.target.value);
    };

    const handleLogin = () => {
        // 示例用户名和密码
        const userName = "testUser";  
        const password = "testPass";  

        // 输入验证：检查是否为1到6之间的数字
        if (number === "" || isNaN(Number(number)) || Number(number) < 1 || Number(number) > 6) {
            alert("请输入一个有效的1-6之间的数字");
            return;
        }

        // 发送请求到后端进行登录
        fetch("/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                userName,
                password,
            }),
        })
            .then((res) => res.json())
            .then((res) => {
                if (Number(res.code) === 0) {
                    // 登录成功，跳转到主页面
                    alert("登录成功: " + userName);
                    router.push("/main");
                } else {
                    alert("登录失败: " + res.info);
                }
            })
            .catch((err) => alert("请求失败: " + err));
    };

    return (
        <div style={{ padding: "20px", textAlign: "center" }}>
            <h1>输入座位号：1-6</h1>
            <input
                type="number"
                value={number}
                onChange={handleChange}
                style={{ width: "200px", padding: "8px", fontSize: "16px", marginBottom: "10px" }}
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
