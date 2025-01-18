import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/router";
import { PieChartOutlined, DashOutlined } from "@ant-design/icons";
import type { MenuProps, DatePickerProps } from "antd";
import { Breadcrumb, Select, DatePicker, Layout, Modal, theme, Input, Avatar, Button, List, Spin, Badge, Divider, Col, Drawer, Row, message } from "antd";
import SiderBar from "../components/SiderBar";
import ReceiverItem from "../components/ReceiverItem";
import SenderItem from "../components/SenderItem";
import { BACKEND_URL } from "../constants/string";
import store from "../redux/store";

const { Search } = Input;
const { Header, Content, Footer, Sider } = Layout;


interface FriendsDataType { // 聊天列表数据类型
    name: string;
    avatar: string;
    id: number;
    unread: number;
    room_type: string;
}

interface SendMsgType { // 已发送待确认的消息列表类型
    type: string;
    room_id: number;
    message: string;
    ack_id: number;
    reply_id: number;
}

interface ChatContentType { // 聊天内容数据类型
    content: string;
    sendId: number;
    msgId: number;
    sender: string;
    avatar: string;
    replyId: number;
    replyMessage: ReplyContentType | null;
    ref?: React.RefObject<HTMLDivElement>;
}
interface ReplyContentType {

    content: string;
    senderName: string;

}
interface ChatHistoryType { // 所有聊天室的历史聊天记录的总和
    room_id: number;
    messages: ChatContentType[];
    reached_end: boolean;
}

interface HistoryMsgType { // 只用于搜索聊天记录
    content: string;
    sender_name: string;
    sender_avatar: string;
    msg_id: number;
    time: string;
}

interface UserDetailType {
    name: string;
    avatar: string;
}
interface MessageDetailType { // 消息详情
    reply_count: number;
    read_users_info: UserDetailType[];
    message_send_time: string;
}
const MainPage: React.FC = () => {
    const router = useRouter();
    const [collapsed, setCollapsed] = useState(true);
    const [myFriends, setMyFriends] = useState<FriendsDataType[]>([]); //聊天列表(包括群和私)
    const {
        token: { colorBgContainer, borderRadiusLG },
    } = theme.useToken();


    const handleItemClick = ({ key }: { key: string }) => {
        // 根据不同的菜单项key执行不同的操作
        switch (key) {
            case "1":
                break;
            case "2":
                break;
            case "3":
                router.push("/grouplist");
                break;
            case "4":
                router.push("/friendslist");
                break;
            case "5":
                router.push("/info");
                break;
            default:
                break;
        }
    };

    /* 聊天主界面 */
    /* 处理发送消息 */
    const [chatContent, setChatContent] = useState<string>(""); // 聊天内容输入
    const [selectedRoom, setSelectedRoom] = useState<FriendsDataType>({ name: "", avatar: "", id: -1, unread: -1, room_type: "" }); // 当前选中的私聊或群聊
    const [userId, setUserId] = useState<number>(store.getState().auth.id); // 本人id，后面再改成从redux获取
    const [myName, setMyName] = useState<string>(store.getState().auth.name); // 本人用户名
    const [messageList, setMessageList] = useState<ChatContentType[]>([]); // 当前窗口的聊天记录
    const [socket, setSocket] = useState<WebSocket | null>(null); // 保存socket连接状态
    const [ackId, setAckId] = useState(-1); // 消息的自减序列，一定是一个负数
    const [toAckMsg, setToAckMsg] = useState<SendMsgType[]>([]); // 已发送待确认的消息列表，用于定时重传
    const [historyList, setHistoryList] = useState<ChatHistoryType[]>([]); // 每个room的历史聊天记录
    const [replyId, setReplyId] = useState<number>(-1); // 回复的消息id
    const [replyMessage, setReplyMessage] = useState<ReplyContentType | null>(null); // 回复的消息内容
    const [contextMenu, setContextMenu] = useState<{ visible: boolean, x: number, y: number }>({ visible: false, x: 0, y: 0 });
    const [clickedMessageItem, setClickedMessageItem] = useState<ChatContentType | null>(null);
    const [detailModal, setDetailModal] = useState(false); //信息详情的模态框
    const [messageDetail, setMessageDetail] = useState<MessageDetailType | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    useEffect(() => {
        setIsLoading(true);
    }, []);
    const onSendMessage = () => {
        if (socket && selectedRoom) {
            const msgid = ackId;
            console.log("回复消息id:", replyId);
            setAckId(ackId - 1);
            const message: SendMsgType = {
                type: "send_message",
                room_id: selectedRoom.id,
                message: chatContent,
                ack_id: msgid,// 一个自减序列
                reply_id: replyId,
            };
            console.log("发送消息:", message);
            socket.send(JSON.stringify(message));
            const newmsg: ChatContentType = {
                content: chatContent,
                sendId: userId,
                msgId: msgid, // 后面改成从服务器获取
                sender: myName,
                avatar: store.getState().auth.avatar,
                replyId,
                replyMessage: replyId === -1 ? null : replyMessage,
            };
            setToAckMsg([...toAckMsg, message]);
            setMessageList([...messageList, newmsg]);
            for (const history of historyList) {
                if (history.room_id === selectedRoom.id) {
                    historyList[historyList.indexOf(history)].messages.push(newmsg);
                    break;
                }
            }
            setChatContent("");
            setReplyMessage(null);
            setReplyId(-1);
        }
        return;
    };

    // 重复发送未ack的消息
    useEffect(() => {
        const toackinterval = setInterval(() => {
            if (socket && toAckMsg.length > 0) {
                for (const msg of toAckMsg) {
                    socket.send(JSON.stringify(msg));
                }
            }
        }, 5000);
        // 清除定时器
        return () => clearInterval(toackinterval);
    }, []);

    // 建立socket连接
    useEffect(() => {
        const params = {
            token: `${store.getState().auth.token}`,
        };
        const queryString = new URLSearchParams(params).toString();
        const urlforws = `wss://my-back-demo-7encent.app.secoder.net/ws/chat/?${queryString}`;
        let ws = new WebSocket(urlforws);
        setSocket(ws);

        const heartbeat = setInterval(() => {
            ws.send(JSON.stringify({ type: "ping" }));
            console.log("发送心跳包ping");
        }, 7500);

        ws.onopen = () => {
            console.log("WebSocket连接已建立");
            // 启动心跳机制
            if (ws && ws.readyState === WebSocket.OPEN) {
                heartbeat;
            }
        };

        ws.onerror = (event: Event) => {
            console.error("WebSocket错误:", event);
        };

        ws.onclose = () => {
            setSocket(null);
            console.log("WebSocket连接已关闭,尝试重新连接");
            clearInterval(heartbeat);
            ws = new WebSocket(urlforws);
            setSocket(ws);
        };

        return () => {
            clearInterval(heartbeat);
            ws.close();
        };

    }, []);

    /* 放置消息监听 */
    useEffect(() => {
        if (socket) {
            socket.onmessage = (event: MessageEvent) => {
                const data = JSON.parse(event.data);
                if (data.type === "room_infos") {
                    // 初始时，收到房间信息
                    console.log("收到room_infos:", data);
                    const fri: FriendsDataType[] = [];
                    for (const room of data.rooms) {
                        fri.push({
                            name: room.name,
                            avatar: room.avatar,
                            id: room.id,
                            unread: 0, // unread_messages里更改
                            room_type: room.room_type,
                        });
                    }
                    console.log("fri:", fri);
                    setMyFriends(fri);
                }
                else if (data.type === "unread_messages") { // 假设room_infos先到达，可能有问题
                    // 初始时，收到未读消息
                    console.log("收到unread_messages:", data);
                    const ack = data.ack_id;
                    socket.send(JSON.stringify({ ack_id: ack, type: "receiver_ack" }));
                    console.log("收到未读消息并返回:", ack);
                    // 进行操作
                    const roomsData = data.unread_messages;
                    const tmphistoryList: ChatHistoryType[] = [];
                    console.log("roomsData:", roomsData);
                    for (const roomdata of roomsData) {
                        const roomid = roomdata.room_id;
                        for (const room of myFriends) {
                            if (room.id === roomid) {
                                myFriends[myFriends.indexOf(room)].unread = roomdata.unread_count;
                                console.log("unread_count:", roomdata.unread_count);
                                break;
                            }
                        }
                        const tmpContent: ChatContentType[] = [];
                        for (const Data of roomdata.values) {
                            tmpContent.push({
                                content: Data.message_content,
                                sendId: Data.sender_id,
                                msgId: Data.message_id,
                                sender: Data.sender_name,
                                avatar: Data.sender_avatar,
                                replyId: Data.reply_id,
                                replyMessage: Data.replied_message ? { content: Data.replied_message.content, senderName: Data.replied_message.sender_name } : null,
                            });
                        }
                        tmpContent.reverse();

                        tmphistoryList.push({ room_id: roomid, messages: tmpContent, reached_end: false });
                    }
                    setHistoryList(tmphistoryList);
                    setIsLoading(false);
                    console.log("收到未读消息并渲染:", tmphistoryList);
                }
                else if (data.type === "chat_message") {
                    // 收到新消息,可能包含自己发的，需要判断
                    console.log("收到chat_message新消息:", data);
                    const senderId = data.sender_id;
                    if (senderId !== userId) { // 不是自己发的
                        const newmsg: ChatContentType = {
                            content: data.message_content,
                            sendId: senderId,
                            msgId: data.message_id,
                            sender: data.sender_name,
                            avatar: data.sender_avatar,
                            replyId: data.reply_id,
                            replyMessage: data.replied_message ? { content: data.replied_message.content, senderName: data.replied_message.sender_name } : null,
                        };
                        console.log("roomid1:", data.room_id);
                        console.log("roomid2:", selectedRoom?.id);
                        if (data.room_id === selectedRoom?.id) { // 收到的消息是当前聊天室的
                            setMessageList([...messageList, newmsg]);
                            message.success(`收到来自${newmsg.sender}的消息`);
                            socket.send(JSON.stringify({ type: "set_read_index", room_id: selectedRoom?.id, read_index: data.message_id }));
                            for (const history of historyList) {
                                if (history.room_id === data.room_id) {
                                    historyList[historyList.indexOf(history)].messages.push(newmsg);
                                    break;
                                }
                            }
                        }
                        else { // 收到的消息不是当前聊天室的
                            // 显示通知
                            for (const room of myFriends) {
                                if (room.id === data.room_id) {
                                    console.log("收到新消息，找到聊天室索引:", myFriends.indexOf(room));
                                    console.log("myFriends:", myFriends);
                                    const Llist = myFriends;
                                    Llist[myFriends.indexOf(room)].unread += 1;
                                    setMyFriends([...Llist]);
                                    break;
                                }
                            }
                            for (const history of historyList) {
                                if (history.room_id === data.room_id) {
                                    historyList[historyList.indexOf(history)].messages.push(newmsg);
                                    break;
                                }
                            }
                        }
                    }
                    else { // 自己发的消息
                        console.log("收到自己发的消息!");
                    }
                    socket.send(JSON.stringify({ ack_id: data.ack_id, type: "receiver_ack" }));
                }
                else if (data.type === "pong") {
                    console.log("收到pong");
                }
                else if (data.type === "acknowledge") {
                    const ackid = data.ack_id;
                    const msgid = data.message_id;
                    console.log("收到确认消息:", ackid, msgid);
                    for (const ackmsg of toAckMsg) {
                        if (ackmsg.ack_id === ackid) {
                            console.log("确认消息成功:", ackmsg);
                            toAckMsg.splice(toAckMsg.indexOf(ackmsg), 1);
                            break;
                        }
                    }
                    for (const history of historyList) {
                        if (history.room_id === selectedRoom?.id) {
                            console.log("roomid3:", selectedRoom?.id);
                            const hislist: ChatHistoryType[] = historyList;
                            for (const message of hislist[historyList.indexOf(history)].messages) {
                                if (message.msgId === ackid) { // 找到对应的消息，更新状态
                                    console.log("找到对应的消息,更新状态ack_id:", ackid);
                                    hislist[historyList.indexOf(history)].messages[hislist[historyList.indexOf(history)].messages.indexOf(message)].msgId = data.message_id;
                                    setHistoryList([...hislist]);
                                    break;
                                }
                            }
                            const msgmsg = hislist[historyList.indexOf(history)].messages;
                            setMessageList(msgmsg);
                            break;
                        }
                    }
                }
                else if (data.type === "message_detail") {
                    console.log("收到message_detail:", data);
                    if (selectedRoom?.room_type === "group") { // 群聊
                        const userDetailData: UserDetailType[] = [];
                        for (const user of data.users_info) {
                            userDetailData.push({
                                name: user.name,
                                avatar: user.avatar,
                            });
                        }
                        const messageDetailData: MessageDetailType = {
                            reply_count: data.count,
                            read_users_info: userDetailData,
                            message_send_time: data.send_time,
                        };
                        setMessageDetail(messageDetailData);
                    }
                    else if (selectedRoom?.room_type === "private") { // 私聊
                        const userDetailData: UserDetailType[] = [];
                        if (data.is_read) {
                            userDetailData.push({
                                name: selectedRoom?.name,
                                avatar: selectedRoom?.avatar,
                            });
                        }
                        const messageDetailData: MessageDetailType = {
                            reply_count: data.count,
                            read_users_info: userDetailData,
                            message_send_time: data.send_time,
                        };
                        setMessageDetail(messageDetailData);
                    }
                    socket.send(JSON.stringify({ ack_id: data.ack_id, type: "receiver_ack" }));
                }
                else if (data.type === "history_messages") {
                    // 收到新的历史消息
                    console.log("收到history_messages:", data);
                    const ack = data.ack_id;
                    socket.send(JSON.stringify({ ack_id: ack, type: "receiver_ack" }));
                    console.log("收到history_messages并返回:", ack);
                    // 进行操作
                    const tmpContent: ChatContentType[] = [];
                    for (const Data of data.messages) {
                        tmpContent.push({
                            content: Data.content,
                            sendId: Data.sender_id,
                            msgId: Data.message_id,
                            sender: Data.sender_name,
                            avatar: Data.sender_avatar,
                            replyId: Data.reply_id,
                            replyMessage: Data.replied_message ? { content: Data.replied_message.content, senderName: Data.replied_message.sender_name } : null,
                        });
                    }
                    tmpContent.reverse();

                    for (const history of historyList) {
                        if (history.room_id === selectedRoom?.id) {
                            const newmessages = [...tmpContent, ...history.messages];
                            historyList[historyList.indexOf(history)].messages = newmessages;
                            if (!data.messages.length) { // 设置消息已经加载完全了
                                historyList[historyList.indexOf(history)].reached_end = true;
                            }
                            setMessageList(newmessages);
                            setIsLoading(false);
                            break;
                        }
                    }
                }
                else if (data.type === "reply_message_context") {
                    // 收到带有定位的历史消息
                    console.log("收到reply_message_context:", data);
                    const ack = data.ack_id;
                    socket.send(JSON.stringify({ ack_id: ack, type: "receiver_ack" }));
                    if (data.error === "true") {
                        message.error("消息已被删除");
                        setIsLoading(false);
                        return;
                    }
                    else {
                        const tmpContent: ChatContentType[] = [];
                        for (const Data of data.messages) {
                            tmpContent.push({
                                content: Data.message_content,
                                sendId: Data.sender_id,
                                msgId: Data.msg_id,
                                sender: Data.sender_name,
                                avatar: Data.sender_avatar,
                                replyId: Data.reply_id,
                                replyMessage: Data.replied_message ? { content: Data.replied_message.content, senderName: Data.replied_message.sender_name } : null,
                            });
                        }
                        tmpContent.reverse();

                        for (const history of historyList) {
                            if (history.room_id === selectedRoom?.id) {
                                const newmessages = [...tmpContent, ...history.messages];
                                historyList[historyList.indexOf(history)].messages = newmessages;
                                setMessageList(newmessages);
                                break;
                            }
                        }
                    }
                }
            };
        }
    }, [socket, selectedRoom, messageList, historyList, myFriends, toAckMsg]);



    // 删除某一条消息
    const deleteMessage = async () => {
        if (clickedMessageItem) {
            try {
                const params = {
                    room_id: String(selectedRoom?.id),
                    message_id: String(clickedMessageItem.msgId),
                };
                console.log("删除消息1:", params);
                console.log("删除消息2:", clickedMessageItem.content);
                const queryString = new URLSearchParams(params).toString();
                const urlforsearch = `${BACKEND_URL}/api/communication/delete/message?${queryString}`;
                const response = await fetch(urlforsearch, {
                    method: "DELETE",
                    headers: {
                        Authorization: `${store.getState().auth.token}`,
                    },
                });
                const bodys = await response.json();
                if (bodys.code === 0) {
                    message.success("删除消息成功");
                }
                else {
                    message.error("删除消息记录失败", bodys.status);
                }
            }
            catch (err) {
                message.error("删除消息记录时发生错误" + err);
                console.error("删除消息记录时发生错误:", err);
            }

            // 在本地将消息删除
            for (const history of historyList) {
                if (history.room_id === selectedRoom?.id) {
                    const messages = history.messages.filter((message) => message.msgId !== clickedMessageItem.msgId);
                    historyList[historyList.indexOf(history)].messages = messages;
                    setHistoryList([...historyList]);
                    setMessageList(messages);
                    break;
                }
            }
        }
    };
    // 获取详情
    const getDetail = () => {
        if (socket) {
            socket.send(JSON.stringify({
                type: "get_message_detail",
                query_message_id: clickedMessageItem?.msgId,
                room_id: selectedRoom?.id,
                room_type: selectedRoom?.room_type,
            }));
            console.log("开始获取详情：", clickedMessageItem?.content);
        }
    };

    /* 搜索聊天记录的抽屉 */
    const [chatHistoryDrawerVisible, setChatHistoryDrawerVisible] = useState(false); // 抽屉，用于展示聊天记录等信息
    const [isHistoryListVisible, setIsInvitationListVisible] = useState(false); // 历史记录列表的弹窗
    const [messageHistoryList, setMessageHistoryList] = useState<HistoryMsgType[]>([]); // 搜索结果
    interface SearchUserHistoryType {
        value: number;
        label: string;
    }
    const [userFromGroup, setUserFromGroup] = useState<SearchUserHistoryType[]>([]); // 群里的用户列表
    const [selectUserHistory, setSelectUserHistory] = useState<number>(-1); // 需要搜索聊天记录的用户,列表的下标
    const [dateStringHistory, setDateStringHistory] = useState<string>(""); // 选择的日期

    // 尝试
    const endOfList = useRef<HTMLDivElement>(null);
    const endOfMessageList = useRef<HTMLDivElement>(null);
    const topOfList = useRef(null);
    useEffect(() => {
        if (endOfList.current) {
            endOfList.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [messageHistoryList]);
    useEffect(() => {
        endOfMessageList.current?.scrollIntoView({ behavior: "smooth" });
    }, [ackId]); // When messageList changes, execute this effect
    const lastMessagePositionRef = useRef<ChatContentType | null>(null);
    const loadHistoricalMessages = () => {
        setIsLoading(true);
        if (selectedRoom.id === -1) {
            setIsLoading(false);
            return;
        }
        let reach_end = false;
        for (const history of historyList) {
            if (history.room_id === selectedRoom?.id) {
                reach_end = history.reached_end;
                break;
            }
        }
        if (reach_end || !messageList.length) {
            message.error("已加载所有历史消息");
        }
        if (socket && messageList.length > 0 && messageList[0].msgId && !reach_end) {
            lastMessagePositionRef.current = messageList[0];
            socket.send(JSON.stringify({
                type: "get_history_messages",
                room_id: selectedRoom?.id,
                end_id: messageList[0].msgId,
            }));
        }
        else {
            setIsLoading(false);
        }
    };
    // 获取聊天记录
    const fetchHistory = async () => {
        console.log("开始获取聊天记录列表");
        try {
            const params = {
                room_id: String(selectedRoom?.id),
            };
            const queryString = new URLSearchParams(params).toString();
            const urlforsearch = `${BACKEND_URL}/api/communication/searchby/room?${queryString}`;
            const response = await fetch(urlforsearch, {
                method: "GET",
                headers: {
                    Authorization: `${store.getState().auth.token}`,
                },
            });
            const bodys = await response.json();
            if (bodys.code === 0) {
                const historyList: HistoryMsgType[] = [];
                for (const message of bodys.messages) {
                    historyList.push({
                        content: message.content,
                        sender_name: message.sender__name,
                        sender_avatar: message.sender__avatar,
                        msg_id: message.msg_id,
                        time: message.create_time,
                    });
                }
                setMessageHistoryList(historyList);
            }
            else {
                message.error("获取聊天记录失败");
            }
        }
        catch (err) {
            message.error("获取聊天记录时发生错误" + err);
        }
    };
    useEffect(() => {
        if (!chatHistoryDrawerVisible) {
            return;
        }
        // 获取群里的用户列表
        const fetchChatroomDetails = async () => {
            if (selectedRoom?.room_type === "private") { // 私聊
                const groupProfileData: SearchUserHistoryType[] = [];
                groupProfileData.push({
                    value: 0, // 代表空的选项
                    label: " ",
                });
                setUserFromGroup(groupProfileData); // 私聊根本不需要这个功能
            }
            else { // 群聊
                const response = await fetch(`${BACKEND_URL}/api/group/room/information`, {
                    method: "POST",
                    headers: {
                        Authorization: `${store.getState().auth.token}`,
                    },
                    body: JSON.stringify({
                        chatroom_id: selectedRoom?.id,
                    }),
                });
                const data = await response.json();
                if (data.code === 0) {
                    const groupProfileData: SearchUserHistoryType[] = [];
                    groupProfileData.push({
                        value: 0, // 代表空的选项
                        label: "全部用户",
                    });
                    for (const member of data.members) {
                        groupProfileData.push({
                            value: member.id,
                            label: member.name,
                        });
                    }
                    setUserFromGroup(groupProfileData);
                }
                else {
                    message.error("筛选聊天记录失败, ", data.info);
                }
            }
        };
        fetchHistory();
        fetchChatroomDetails();
    }, [chatHistoryDrawerVisible, isHistoryListVisible, selectedRoom]);

    // 更改选择的日期
    const onchangeDate: DatePickerProps["onChange"] = (date, dateString) => {
        console.log("data:", date);
        console.log("选择的日期:", dateString);
        setDateStringHistory(String(dateString));
    };

    // 按用户搜索聊天记录
    const searchHistoryByUser = async () => {
        if (selectUserHistory !== 0) {
            try {
                const userid = selectUserHistory;
                const params = {
                    room_id: String(selectedRoom?.id),
                    member_user_id: String(userid),
                };
                const queryString = new URLSearchParams(params).toString();
                const urlforsearch = `${BACKEND_URL}/api/communication/searchby/member?${queryString}`;
                const response = await fetch(urlforsearch, {
                    method: "GET",
                    headers: {
                        Authorization: `${store.getState().auth.token}`,
                    },
                });
                const bodys = await response.json();
                if (bodys.code === 0) {
                    console.log("成功聊天记录");
                    const historyList: HistoryMsgType[] = [];
                    for (const message of bodys.messages) {
                        historyList.push({
                            content: message.content,
                            sender_name: message.sender__name,
                            sender_avatar: message.sender__avatar,
                            msg_id: message.msg_id,
                            time: message.create_time,
                        });
                    }
                    setMessageHistoryList(historyList);
                }
                else {
                    message.error("获取聊天记录失败");
                }
            }
            catch (err) {
                message.error("获取聊天记录时发生错误" + err);
                console.error("获取聊天记录时发生错误:", err);
            }
        }
        else { // 按用户搜索为空则返回所有
            fetchHistory();
        }
    };

    // 按时间搜索聊天记录
    const searchHistoryByTime = async () => {
        try {
            const params = {
                room_id: String(selectedRoom?.id),
                date: dateStringHistory,
            };
            console.log("搜索参数:", params);
            const queryString = new URLSearchParams(params).toString();
            const urlforsearch = `${BACKEND_URL}/api/communication/searchby/date?${queryString}`;
            const response = await fetch(urlforsearch, {
                method: "GET",
                headers: {
                    Authorization: `${store.getState().auth.token}`,
                },
            });
            const bodys = await response.json();
            if (bodys.code === 0) {
                console.log("成功聊天记录");
                const historyList: HistoryMsgType[] = [];
                for (const message of bodys.messages) {
                    historyList.push({
                        content: message.content,
                        sender_name: message.sender__name,
                        sender_avatar: message.sender__avatar,
                        msg_id: message.msg_id,
                        time: message.create_time,
                    });
                }
                setMessageHistoryList(historyList);
                console.log("按时间搜索历史记录列表:", historyList);
            }
            else {
                message.error("获取聊天记录失败");
            }
        }
        catch (err) {
            message.error("获取聊天记录时发生错误" + err);
            console.error("获取聊天记录时发生错误:", err);
        }
    };

    const [pendingReplyId, setPendingReplyId] = useState<number | null>(null);
    useEffect(() => {
        if (pendingReplyId) {
            const replyMessage = messageList.find(msg => msg.msgId === pendingReplyId);
            if (replyMessage && replyMessage.ref && replyMessage.ref.current) {
                replyMessage.ref.current.scrollIntoView();
                setIsLoading(false);
                message.success("已定位到回复的消息");
                replyMessage.ref.current.style.backgroundColor = "lightgrey";
                setTimeout(() => {
                    if (replyMessage.ref && replyMessage.ref.current) {
                        replyMessage.ref.current.style.backgroundColor = "";
                    }
                }, 500);
                setPendingReplyId(null); // 重置 pendingReplyId
                console.log(messageList);
            }
        }
    }, [messageList, pendingReplyId]);
    /* 点击回复的消息跳转到对应的消息处 */


    const handleReplyItemClick = (item: ChatContentType) => {
        setIsLoading(true);
        console.log("点击的消息的msgid:", item.msgId);
        console.log("回复的消息的msgid:", item.replyId);
        if (item.replyId) {
            const found = messageList.find(msg => msg.msgId === item.replyId);
            if (found) {
                console.log("前端有这个消息，直接跳转");
                setPendingReplyId(item.replyId);
            }
            else {
                if (socket) {
                    socket.send(JSON.stringify({
                        type: "get_reply_message",
                        reply_message_id: item.replyId,
                        room_id: selectedRoom?.id,
                        end_id: messageList[0].msgId,
                    }));
                    setPendingReplyId(item.replyId); // 设置 pendingReplyId
                }
            }
        }
    };
    /* 点击头像加好友 */
    const clickItemAvatar = async (item: ChatContentType) => {
        console.log("通过群聊sendFriendsRequest");
        await fetch(`${BACKEND_URL}/api/friends/request/friend`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `${store.getState().auth.token}`,
            },
            body: JSON.stringify({
                to_user_id: item.sendId,
            }),
        })
            .then((res) => res.json())
            .then((res) => {
                console.log("发送好友请求成功");
                if (Number(res.code) === 0) {
                    message.success("申请发送成功");
                    console.log("fasong好友请求chenggong");
                }
                else {
                    message.error(res.code + " " + res.info);
                    console.log("fasong好友请求失败:", res.info);
                }
            })
            .catch((err) => message.error("申请发送错误：" + err));
    };



    return (
        <Layout style={{ minHeight: "95vh" }}>
            <SiderBar defaultKey={"1"} handleItemClick={handleItemClick} >
                <div className="demo-logo-vertical" />
            </SiderBar>
            <Sider style={{ overflow: "auto", backgroundColor: "lightgrey" }}>
                <div className="list-vertical" />
                <List
                    dataSource={myFriends}
                    renderItem={(item) => (
                        <List.Item
                            key={item.id}
                            style={item.id === selectedRoom?.id ? { backgroundColor: "grey" } : { backgroundColor: "lightgrey" }}
                            onClick={() => {
                                console.log("选择的聊天室id:", item.id);
                                setSelectedRoom(item);

                                // 加载历史消息
                                let lastmsgid;
                                for (const history of historyList) {
                                    if (history.room_id === item.id) {
                                        console.log("ddddd:", history.messages);
                                        setMessageList(history.messages);
                                        if (history.messages.length > 0) {
                                            if (history.messages[history.messages.length - 1].msgId) {
                                                lastmsgid = history.messages[history.messages.length - 1].msgId;
                                            }
                                        }
                                        break;
                                    }
                                }
                                if (item.unread) {
                                    for (const room of myFriends) {
                                        if (room.id === item.id) {
                                            myFriends[myFriends.indexOf(room)].unread = 0;
                                        }
                                    }
                                    //告诉后端已读
                                    if (socket && lastmsgid) {
                                        socket.send(JSON.stringify({ type: "set_read_index", room_id: item.id, read_index: lastmsgid }));
                                        console.log("后端设置为已读，已读索引:", lastmsgid);
                                    }
                                }

                            }} >
                            <Badge count={item.unread} size="default">
                                <Avatar shape="square" size="large" src={item.avatar} />
                            </Badge>
                            <List.Item.Meta title={item.name} style={{ marginLeft: "10px" }} />
                        </List.Item>
                    )}
                />
            </Sider>
            <Layout>
                <Header style={{ background: "white", height: "10vh", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                        {selectedRoom.id !== -1 && <span style={{ color: "gray" }}>{selectedRoom.room_type === "private" ? "User / " : "Group / "}</span>}
                        <span>{selectedRoom.id !== -1 && selectedRoom.name}</span>
                    </div>
                    {selectedRoom.id !== -1 && (
                        <Button onClick={() => { setChatHistoryDrawerVisible(true); }}>
                            聊天记录
                        </Button>
                    )}
                </Header>
                <Drawer width={640} placement="right" closable={false} onClose={() => { setChatHistoryDrawerVisible(false); }} open={chatHistoryDrawerVisible}>
                    <Button
                        type="primary"
                        onClick={() => {
                            setIsInvitationListVisible(true);
                        }}>
                        聊天记录
                    </Button>
                </Drawer>
                <Modal footer={null}
                    title="Chat Message History"
                    open={isHistoryListVisible}
                    onCancel={() => setIsInvitationListVisible(false)}
                    style={{ display: "flex", flexDirection: "column" }}>
                    <Select
                        defaultValue=""
                        style={{ width: 120 }}
                        onChange={(e) => {
                            setSelectUserHistory(Number(e));
                            console.log("选择的用户:", e);
                        }}
                        options={userFromGroup}
                    />
                    <DatePicker onChange={onchangeDate} />
                    <Button onClick={() => {
                        searchHistoryByUser();
                    }}>按用户搜索</Button>
                    <Button onClick={() => {
                        searchHistoryByTime();
                    }}>按时间搜索</Button>
                    <div style={{ height: "400px", overflow: "auto", display: "flex", flexDirection: "column" }}>
                        {messageHistoryList.map((item, index) => (
                            <div key={index} style={{ display: "flex", flexDirection: "row" }}>
                                <Avatar src={item.sender_avatar} />
                                <div style={{ display: "flex", flexDirection: "column" }}>
                                    <div>{item.sender_name}</div>
                                    <div>{item.content}</div>
                                </div>
                            </div>
                        ))}
                        <div ref={endOfList} />
                    </div>
                </Modal>
                <Content style={{ margin: "0 16px", height: "55vh" }}>
                    <div style={{
                        position: "relative",
                        display: "flex",
                        flexDirection: "column",
                        justifyContent: "space-between",
                        height: "100%",
                        minWidth: "900px",
                        minHeight: "100%",
                        background: "#fff"
                    }}>
                        <div id="chatItems" style={{ position: "relative", padding: "20px", overflowY: "auto", background: "#fff", height: "55vh" }}>
                            {
                                <div style={{ position: "absolute", left: "50 %", paddingTop: "50px", textAlign: "center" }}>
                                    {/* <Spin /> */}
                                </div>
                            }
                            {selectedRoom.id !== -1 && (
                                <div ref={topOfList} style={{ display: "flex", justifyContent: "center" }}>
                                    <button onClick={loadHistoricalMessages} style={{ border: "none" }}>加载历史消息</button>
                                </div>
                            )}
                            {Array.isArray(messageList) &&
                                messageList.map((item, index) => {
                                    const messageRef = React.createRef<HTMLDivElement>();
                                    item.ref = messageRef; // 将ref添加到消息对象中

                                    return item.sendId !== userId ? (
                                        <div ref={messageRef} onContextMenu={(e) => {
                                            e.preventDefault();
                                            setClickedMessageItem(item);
                                            setContextMenu({ visible: true, x: e.clientX, y: e.clientY });
                                        }}
                                            style={{ margin: 0, padding: "6px", background: "#fff", borderRadius: "4px" }} key={item.msgId || index}>
                                            <ReceiverItem
                                                clickItemAvatar={clickItemAvatar}
                                                roomId={selectedRoom?.id}
                                                userName={item.sender}
                                                item={item}
                                                avatar={item.avatar}
                                                handleReplyItemClick={handleReplyItemClick} />
                                        </div>
                                    ) : (
                                        <div ref={messageRef} onContextMenu={(e) => {
                                            e.preventDefault();
                                            setClickedMessageItem(item);
                                            setContextMenu({ visible: true, x: e.clientX, y: e.clientY });

                                        }}
                                            style={{ margin: 0, padding: "6px", background: "#fff", borderRadius: "4px" }} key={item.msgId}>
                                            <SenderItem userName={myName} item={item} avatar={store.getState().auth.avatar} handleReplyItemClick={handleReplyItemClick} />
                                        </div>
                                    );
                                })
                            }
                            <div ref={endOfMessageList} />
                            {contextMenu.visible && (
                                <div style={{ position: "fixed", top: contextMenu.y, left: contextMenu.x }}>
                                    <button onClick={() => {
                                        setContextMenu(prevState => ({ ...prevState, visible: false }));
                                        setReplyId(clickedMessageItem?.msgId || -1);
                                        setReplyMessage({
                                            content: clickedMessageItem?.content || "",
                                            senderName: clickedMessageItem?.sender || ""
                                        });
                                    }}>回复</button>
                                    <button onClick={() => {
                                        setContextMenu(prevState => ({ ...prevState, visible: false }));
                                        // 处理删除逻辑
                                        deleteMessage();
                                    }}>删除</button>
                                    <button onClick={() => {
                                        setContextMenu(prevState => ({ ...prevState, visible: false }));
                                        getDetail();
                                        setDetailModal(true);
                                    }}>详情</button>
                                </div>
                            )}
                            {detailModal && (
                                <Modal footer={null}
                                    title="详情"
                                    open={detailModal}
                                    onCancel={() => setDetailModal(false)}
                                >
                                    {/* 在这里添加你的详情内容 */}
                                    <p>该消息被回复数量：{messageDetail?.reply_count}</p>
                                    <p>发送时间：{messageDetail?.message_send_time}</p>
                                    <p>已读用户：</p>
                                    {messageDetail?.read_users_info.map((user, index) => (
                                        <div key={index} style={{ display: "flex", flexDirection: "row" }}>
                                            <Avatar src={user.avatar} alt={user.name} />
                                            <p>{user.name}</p>
                                        </div>
                                    ))}
                                </Modal>
                            )}
                        </div>
                    </div>
                </Content>
                <Footer style={{ padding: 0, background: colorBgContainer, textAlign: "left", height: "30vh", display: "flex", flexDirection: "column", justifyContent: "flex-end" }}>
                    <div style={{ marginLeft: "10px", marginRight: "10px" }}>
                        {selectedRoom.id !== -1 && (
                            <>
                                {replyMessage && (
                                    <div>
                                        <p>{replyMessage.senderName}:{replyMessage.content}</p>
                                        <button onClick={() => {
                                            setReplyMessage(null);
                                            setReplyId(-1);
                                        }}>取消回复
                                        </button>
                                    </div>
                                )}
                                <Row>
                                    <Input.TextArea
                                        placeholder="请输入消息"
                                        autoSize={{ minRows: 4, maxRows: 5 }}
                                        value={chatContent}
                                        onChange={(e) => (
                                            // dispatch({
                                            //     type: "chat/chatInputMessageChange",
                                            //     payload: {
                                            //         message: e.target.value,
                                            //     },
                                            // })
                                            setChatContent(e.target.value))
                                        }
                                    />
                                </Row>
                                <Row justify="end" style={{ marginTop: 10, marginRight: 10 }}>
                                    <Col>
                                        <Button type="primary" onClick={onSendMessage} disabled={!chatContent}>
                                            发送
                                        </Button>
                                        {/* for test */}
                                        {/* <Button type="primary" onClick={onMessageScroll}>滚动</Button> */}
                                    </Col>
                                </Row>
                            </>
                        )}
                    </div>
                </Footer>
            </Layout>
            {isLoading && (
                <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: "rgba(0, 0, 0, 0.5)", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", zIndex: 9999 }}>
                    <Spin style={{ fontSize: "2em" }} />
                    <div>Loading...</div>
                </div>
            )}
        </Layout>

    );
};

export default MainPage;
