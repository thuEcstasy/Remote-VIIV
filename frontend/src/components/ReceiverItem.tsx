import { Avatar, Modal, Button } from "antd";
import MessageView from "./MessageView";
import React, { useState } from "react";
import { BACKEND_URL } from "../constants/string";
import store from "../redux/store";

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
interface ReceiverItemProps {
    userName: string;
    item: ChatContentType;
    avatar: string;
    handleReplyItemClick: (item: ChatContentType) => void;
    roomId: number;
    clickItemAvatar: (item: ChatContentType) => void;
}

const ReceiverItem: React.FC<ReceiverItemProps> = ({ userName, item, avatar, roomId, handleReplyItemClick, clickItemAvatar }) => {
    const [openModal, setOpenModal] = useState(false); // 点击头像打开信息框
    const [isFriend, setIsFriend] = useState(false); // 是否是好友

    // 检查是否是好友
    const checkFriend = async (item: ChatContentType) => {
        // TODO: 发送请求，检查是否是好友
        const params = {
            member_id: String(item.sendId),
            room_id: String(roomId),
        };
        const queryString = new URLSearchParams(params).toString();
        const urlforsearch = `${BACKEND_URL}/api/group/judge/friend?${queryString}`;
        const response = await fetch(urlforsearch, {
            method: "GET",
            headers: {
                Authorization: `${store.getState().auth.token}`,
            },
        });
        const bodys = await response.json();

        console.log("check friend:", bodys);
        if (bodys.code === 0) {
            if (bodys.is_friend) {
                setIsFriend(true);
            }
            else {
                setIsFriend(false);
            }
        }
        else {
            console.error("获取失败");
        }
    };


    return (
        <div style={{ position: "relative", display: "flex", alignItems: "flex-start" }}>
            {/* receiver */}
            <div style={{ width: "48px", marginRight: "8px" }}>
                <Avatar
                    onClick={() => {
                        setOpenModal(true);
                        checkFriend(item);
                    }}
                    src={avatar}
                    size="large"
                    style={{ backgroundColor: "#005EFF", verticalAlign: "middle" }}>
                </Avatar>
            </div>
            <Modal
                title="User Info"
                open={openModal}
                onCancel={() => setOpenModal(false)}
            >
                <Avatar src={avatar}></Avatar>
                <p>User Name:{item.sender}</p>
                <Button
                    className={"add-friend"}
                    key={"add-friend-btn"}
                    onClick={() => {
                        clickItemAvatar(item);
                    }}
                    disabled={isFriend}>
                    好友申请
                </Button>
            </Modal>
            <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "flex-start" }}>
                <text style={{ fontSize: "10px" }}>
                    {userName}
                </text>
                <MessageView type="text" isSender={false} item={item} />
                {item.replyId !== -1 && item.replyMessage && (
                    <div
                        style={{ marginTop: "10px", padding: "10px", background: "#f0f0f0", borderRadius: "4px", display: "flex", justifyContent: "flex-start", maxWidth: "50%", alignSelf: "flex-start", cursor: "pointer" }}
                        onClick={() => {
                            console.log("点击回复，跳转到回复消息的位置");
                            //TODO
                            handleReplyItemClick(item);
                        }}
                    >
                        <p style={{
                            margin: 0,
                            maxWidth: "200px",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap"
                        }}>
                            <strong>{item.replyMessage.senderName}:</strong> {item.replyMessage.content}
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ReceiverItem;

