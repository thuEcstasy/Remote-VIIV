import { useState } from "react";
import { BACKEND_URL, FAILURE_PREFIX, LOGIN_FAILED, LOGIN_SUCCESS_PREFIX } from "../constants/string";
import { useRouter } from "next/router";
import { setName, setToken, setEmail, setPhone, setAvatar, setId } from "../redux/auth";
import { useDispatch } from "react-redux";
import { message } from "antd";
import { NetworkError, NetworkErrorType, request } from "../utils/network";
import styles from "../styles/LoginPage.module.css";

const LoginScreen = () => {
    const [userName, setUserName] = useState("");
    const [password, setPassword] = useState("");
    const [errorMessage, setErrorMessage] = useState("");

    const router = useRouter();
    const dispatch = useDispatch();

    const login = () => {
        if (userName === "" || password === "") {
            message.error("用户名和密码不能为空");
            return;
        }
        fetch(`${BACKEND_URL}/api/author/login`, {
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
                    dispatch(setName(userName));
                    dispatch(setToken(res.token));
                    dispatch(setEmail(res.data.email));
                    console.log("email:" + res.email);
                    dispatch(setPhone(res.data.phone_number));
                    dispatch(setAvatar(res.data.avatar));
                    dispatch(setId(res.data.id));
                    message.success(LOGIN_SUCCESS_PREFIX + userName);
                    router.push("/main");
                }
                else {
                    message.error("登录失败: " + res.info);
                }
            })
            .catch((err) => alert(FAILURE_PREFIX + err));
    };

    return (
        <div className={styles.container}>
            <h2>Login</h2>
            <form className={styles.form} onSubmit={(e) => e.preventDefault()}>
                <div className={styles.group}>
                    <label htmlFor="username">Username:</label><br />
                    <input
                        type="text"
                        id="username"
                        className={styles.control}
                        value={userName}
                        onChange={(e) => setUserName(e.target.value)}
                    />
                </div>
                <div className={styles.group}>
                    <label htmlFor="password">Password:</label><br />
                    <input
                        type="password"
                        id="password"
                        className={styles.control}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                </div><br />
                {errorMessage && <div className={styles.error}>{errorMessage}</div>}
                <button className={`${styles.btn} ${styles.btnp}`} onClick={login}>
                    Login
                </button><br />
                <button className={`${styles.btn}`} onClick={() => router.push("/register")}>
                    Register
                </button>
            </form>
        </div>
    );
};

export default LoginScreen;
