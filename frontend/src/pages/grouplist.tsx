
import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/router";
import { PieChartOutlined, UserAddOutlined, PlusOutlined } from "@ant-design/icons";
import type { InputRef } from "antd";
import { Form, Breadcrumb, Flex, Tooltip, Layout, message, Tag, theme, Input, Avatar, Button, List, Badge, Divider, Col, Drawer, Row, Modal } from "antd";
import SiderBar from "../components/SiderBar";
import { BACKEND_URL } from "../constants/string";
import store from "../redux/store";



const { Sider, Header, Content } = Layout;
const { Search } = Input;

interface DescriptionItemProps {
    title: string;
    content: React.ReactNode;
}

const DescriptionItem = ({ title, content }: DescriptionItemProps) => (
    <div className="site-description-item-profile-wrapper">
        <p className="site-description-item-profile-p-label" style={{ fontWeight: "bold" }}>{title}:</p>
        {content}
    </div>
);

/* 搜索添加好友列表 */
interface GroupsDataType {
    name: string;
    avatar: string;
    sendStatus: string;
    id: number;
    status: number;
}
interface FriendsDataType {
    name: string;
    avatar: string;
    sendStatus: string;
    id: number;
    status: number;
}
interface MemberType {
    id: number;
    name: string;
    role: string
}
interface NoticeType {
    create_time: string;
    title: string;
    text: string;

}
interface GroupProfileDataType {
    member: MemberType[];
    notice: NoticeType[];
}
interface InvitationDataType {
    invitation_id: number;
    invited_user_id: number;
    invited_username: string;
    inviter_user_id: number;
    inviter_username: string;
    chatroom_id: number;
    chatroom_name: string;
    create_time: string;
}
type PaginationPosition = "top" | "bottom" | "both";
type PaginationAlign = "start" | "center" | "end";

/* 标签 */
const tagInputStyle: React.CSSProperties = {
    width: 64,
    height: 22,
    marginInlineEnd: 8,
    verticalAlign: "top",
};

const GroupListPage: React.FC = () => {
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [myGroups, setMyGroups] = useState<GroupsDataType[]>([]); //群聊列表
    const [userdata, setUserData] = useState<FriendsDataType[]>([]); //搜索的用户列表
    const [position, setPosition] = useState<PaginationPosition>("bottom");
    const [align, setAlign] = useState<PaginationAlign>("center");
    const [open, setOpen] = useState(false); // 抽屉，展示详细的好友信息
    const [childrenDrawer, setChildrenDrawer] = useState(false); // 二级抽屉，添加标签
    const [UnackList, setUnackList] = useState(false); // 抽屉，展示待通过的好友申请列表
    const [unack, setUnAck] = useState<FriendsDataType[]>([]); // 待通过的好友申请列表
    const [toAccept, setToAccept] = useState<number>(-1); // 处理好友申请
    const [AckRefuse, setAckRefuse] = useState<string>(""); //接受或拒绝好友申请
    const [GroupsProfile, setGroupsProfile] = useState<GroupsDataType>(); // 群聊详细信息
    const [UserProfile, setUserProfile] = useState<number>(-1); // 用户详细信息
    const [myFriends, setMyFriends] = useState<FriendsDataType[]>([]); //好友列表
    const [isModal1Visible, setIsModal1Visible] = useState(false);
    const [isModal3Visible, setIsModal3Visible] = useState(false);
    const [isModal4Visible, setIsModal4Visible] = useState(false);
    const [isNoticeBoardOpen, setNoticeBoardOpen] = useState(false);
    const [isTransOwnerModalVisible, setTransOwnerModalVisible] = useState(false);
    const [isInvitationListVisible, setIsInvitationListVisible] = useState(false);
    const [roomId, setRoomId] = useState<number>(-1);
    const [chatroomDetails, setChatroomDetails] = useState<GroupProfileDataType | null>(null);
    const [invitationList, setInvitationList] = useState<InvitationDataType[]>([]);
    const [myRoomIdentity, setMyRoomIdentity] = useState<{ is_owner: boolean, is_admin: boolean }>({ is_owner: false, is_admin: false });
    /* 根据不同的菜单项key执行不同的操作 */
    const handleItemClick = ({ key }: { key: string }) => {
        switch (key) {
            case "1":
                router.push("/main");
                break;
            case "2":
                break;
            case "3":
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
    const fetchChatroomDetails = async (roomId: number) => {
        const response = await fetch(`${BACKEND_URL}/api/group/room/information`, {
            method: "POST",
            headers: {
                Authorization: `${store.getState().auth.token}`,
            },
            body: JSON.stringify({
                chatroom_id: roomId,
            }),
        });
        const data = await response.json();
        if (data.code === 0) {
            const groupProfileData: GroupProfileDataType = {
                member: data.members.map((member: { id: any; name: any; role: string }) => ({
                    id: member.id,
                    name: member.name,
                    role: member.role,
                })),
                notice: data.notices.map((notice: { create_time: any; title: any; text: any; }) => ({
                    create_time: notice.create_time,
                    title: notice.title,
                    text: notice.text,
                })),
            };
            setChatroomDetails(groupProfileData);
        }
        else {
            message.error(data.info);
        }
    };
    const fetchMyRoomIdentity = async (roomId: number) => {
        const response = await fetch(`${BACKEND_URL}/api/group/get/identity?room_id=${roomId}`, {
            method: "GET",
            headers: {
                Authorization: `${store.getState().auth.token}`,
            },
        });
        const data = await response.json();
        if (data.code === 0) {
            setMyRoomIdentity({
                is_owner: data.is_owner,
                is_admin: data.is_admin,
            });
        }
        else {
            message.error(data.info);
        }
    };
    useEffect(() => {
        if (UnackList) {
            return;
        }
        if (open) {
            return;
        }
        const fetchFriends = async () => {
            console.log("开始获取好友列表");
            try {
                const response = await fetch(`${BACKEND_URL}/api/friends/friend/list_all`, {
                    method: "GET",
                    headers: {
                        Authorization: `${store.getState().auth.token}`,
                    },
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const bodys = await response.json();

                if (bodys.code === 0) {
                    const friList: FriendsDataType[] = [];
                    for (const body of bodys.members) {
                        const myfri: FriendsDataType = {
                            name: body.username,
                            avatar: body.avatar,
                            id: body.id,
                            status: body.status, // 待修改
                            sendStatus: "", // 待修改
                        };
                        if (myfri.status === 0) {
                            myfri.sendStatus = "send request";
                        }
                        else if (myfri.status === 1) {
                            myfri.sendStatus = "already friend";
                        }
                        else if (myfri.status === 2) {
                            myfri.sendStatus = "waiting for response";
                        }
                        friList.push(myfri);
                    }
                    setMyFriends([...friList]); //后期改成请求
                    console.log("我的好友初始化成功");
                    console.log(friList);

                }
                else {
                    message.error(bodys.info);
                }
            }
            catch (err) {
                message.error("获取好友列表时发生错误");
            }
        };

        fetchFriends();
    }, [UnackList, open]);
    /* 初始化好友列表 */
    useEffect(() => {
        if (UnackList) {
            return;
        }
        if (open) {
            return;
        }
        const fetchGroups = async () => {
            console.log("开始获取群聊列表");
            try {
                const response = await fetch(`${BACKEND_URL}/api/group/room/getall`, {
                    method: "GET",
                    headers: {
                        Authorization: `${store.getState().auth.token}`,
                    },
                });
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const bodys = await response.json();

                if (bodys.code === 0) {
                    const groupList: GroupsDataType[] = [];
                    for (const body of bodys.chatrooms) {
                        const mygroup: GroupsDataType = {
                            name: body.name,
                            avatar: body.avatar,
                            id: body.id,
                            status: 0, // 待修改
                            sendStatus: "", // 待修改
                        };
                        groupList.push(mygroup);
                    }
                    setMyGroups([...groupList]); //后期改成请求
                    message.success("我的群聊初始化成功");
                }
                else {
                    message.error("获取群聊失败:" + String(bodys.code) + String(bodys.info));
                }
            }
            catch (err) {
                message.error("获取群聊列表时发生错误");
            }
        };

        fetchGroups();
    }, [UnackList, open]);

    /* 通过申请 */
    useEffect(() => {
        if (toAccept === -1) {
            return;
        }
        acceptFriend();
    }, [toAccept]);

    const acceptFriend = async () => {
        await fetch(`${BACKEND_URL}/api/friends/request/friend/handle`, {
            method: "POST",
            headers: {
                Authorization: `${store.getState().auth.token}`,
            },
            body: JSON.stringify({
                request_id: toAccept.toString(),
                action: AckRefuse,
            }),
        })
            .then((res) => res.json())
            .then((res) => {
                if (Number(res.code) === 0) {
                    if (AckRefuse === "accept") {
                        message.success("好友申请已通过");
                    }
                    else {
                        message.success("好友申请已拒绝");
                    }
                }
                else {
                    message.error(res.code + " " + res.info);
                }
            })
            .catch((err) => message.error("处理好友申请失败"));
    };
    function inviteUserList() {
        setIsModal1Visible(true);
    }
    function manageAdminList() {
        setIsModal3Visible(true);
    }
    function removeMemberList() {
        setIsModal4Visible(true);
    }
    function writeNoticeBoard() {
        setNoticeBoardOpen(true);
    }
    function transOwnerList() {
        setTransOwnerModalVisible(true);
    }
    function handleOpenModal() {
        setIsInvitationListVisible(true);
    }
    const inviteFriend = async (friend: FriendsDataType, roomId: number) => {
        try {
            const response = await fetch(`${BACKEND_URL}/api/group/room/invite`, {
                method: "POST",
                headers: {
                    Authorization: `${store.getState().auth.token}`,
                },
                body: JSON.stringify({
                    friend_id: friend.id,
                    chatroom_id: roomId
                }),
            });
            const data = await response.json();
            if (data.code === 0) {
                if (data.message === "Invitation sent, waiting for approval") {
                    message.success("邀请发送成功");
                    setIsModal1Visible(false);
                }
                else {
                    message.success("已添加成员");
                    setIsModal1Visible(false);
                }
                fetchChatroomDetails(roomId);
            }
            else {
                message.error("邀请发送失败:" + data.code + data.info);
            }
        }
        catch (err) {
            message.error("发送邀请时发生错误");
        }
    };
    const manageAdmin = async (userId: number, roomId: number) => {
        try {
            const response = await fetch(`${BACKEND_URL}/api/group/room/setadmins`, {
                method: "POST",
                headers: {
                    Authorization: `${store.getState().auth.token}`,
                },
                body: JSON.stringify({
                    admin_ids: [userId],
                    chatroom_id: roomId
                }),
            });
            const data = await response.json();
            if (data.code === 0) {
                message.success("成功设置为管理员");
                setIsModal3Visible(false);
                fetchChatroomDetails(roomId);
            }
            else {
                message.error("设置管理员失败:" + String(data.code) + String(data.info));
            }
        }
        catch (err) {
            message.error("设置管理员时发生错误");
        }
    };
    const removeMember = async (userId: number, roomId: number) => {
        try {
            const response = await fetch(`${BACKEND_URL}/api/group/room/remove`, {
                method: "POST",
                headers: {
                    Authorization: `${store.getState().auth.token}`,
                },
                body: JSON.stringify({
                    member_id: userId,
                    chatroom_id: roomId
                }),
            });
            const data = await response.json();
            if (data.code === 0) {
                message.success("成功踢出用户");
                setIsModal4Visible(false);
                fetchChatroomDetails(roomId);
            }
            else {
                message.error("踢出用户失败:" + String(data.code) + String(data.info));
            }
        }
        catch (err) {
            message.error("踢出用户时发生错误");
        }
    };
    const leaveGroup = async () => {
        try {
            const response = await fetch(`${BACKEND_URL}/api/group/room/leave`, {
                method: "POST",
                headers: {
                    Authorization: `${store.getState().auth.token}`,
                },
                body: JSON.stringify({
                    chatroom_id: roomId
                }),
            });
            const data = await response.json();
            if (data.code === 0) {
                message.success("成功退出群聊");
                fetchChatroomDetails(roomId);
            }
            else {
                message.error("退出群聊失败:" + String(data.code) + String(data.info));
            }
        }
        catch (err) {
            message.error("退出群聊时发生错误");
        }
    };
    const writeNotice = async (title: string, text: string, roomId: number) => {
        try {
            const response = await fetch(`${BACKEND_URL}/api/group/room/post/notice`, {
                method: "POST",
                headers: {
                    Authorization: `${store.getState().auth.token}`,
                },
                body: JSON.stringify({
                    chatroom_id: roomId,
                    title,
                    text
                }),
            });
            const data = await response.json();
            if (data.code === 0) {
                message.success("发送公告成功");
                setNoticeBoardOpen(false);
                fetchChatroomDetails(roomId);
            }
            else {
                message.error("发送公告失败:" + String(data.code) + String(data.info));
            }
        }
        catch (err) {
            message.error("发送公告时发生错误");
        }
    };
    const transOwner = async (newOwnerId: number) => {
        try {
            const response = await fetch(`${BACKEND_URL}/api/group/room/transfer`, {
                method: "POST",
                headers: {
                    Authorization: `${store.getState().auth.token}`,
                },
                body: JSON.stringify({
                    chatroom_id: roomId,
                    new_owner_id: newOwnerId
                }),
            });
            const data = await response.json();
            if (data.code === 0) {
                message.success("成功转移群主");
                setTransOwnerModalVisible(false);
                fetchChatroomDetails(roomId);
            }
            else {
                message.error("转移群主失败:" + String(data.code) + String(data.info));
            }
        }
        catch (err) {
            message.error("转移群主时发生错误");
        }
    };
    const fetchInvitationList = async () => {
        try {
            const response = await fetch(`${BACKEND_URL}/api/group/room/get/invitation`, {
                method: "GET",
                headers: {
                    Authorization: `${store.getState().auth.token}`,
                },
            });
            const data = await response.json();
            if (data.code === 0) {
                message.success("获取群聊申请信息成功");
                setInvitationList(data.pending_invitations);
            }
            else {
                message.error("发送公告失败:" + String(data.code) + String(data.info));
            }
        }
        catch (err) {
            message.error("发送公告时发生错误:");
        }
    };
    useEffect(() => {
        fetchInvitationList();
    }, []);
    const handleAccept = async (invitationId: number, action: string) => {
        try {
            const response = await fetch(`${BACKEND_URL}/api/group/room/handle`, {
                method: "POST",
                headers: {
                    Authorization: `${store.getState().auth.token}`,
                },
                body: JSON.stringify({
                    invitation_id: invitationId,
                    action
                }),
            });
            const data = await response.json();
            if (data.code === 0) {
                message.success("处理邀请成功");
                setIsInvitationListVisible(false);
                fetchInvitationList();
            }
            else {
                message.error("处理邀请失败:" + String(data.code) + String(data.info));
            }
        }
        catch (err) {
            message.error("处理邀请时发生错误");
        }
    };
    return (
        <Layout style={{ minHeight: "95vh" }}>
            <SiderBar defaultKey={"3"} handleItemClick={handleItemClick} >
                <div className="demo-logo-vertical" />
            </SiderBar>
            <Sider style={{ overflow: "auto", backgroundColor: "lightgrey" }}>
                <div className="list-vertical" />
                <List
                    dataSource={myGroups}
                    renderItem={(item) => (
                        <List.Item
                            key={item.id}
                            style={item.id === GroupsProfile?.id ? { backgroundColor: "grey" } : {backgroundColor:"lightgrey"}}
                            onClick={() => {
                                setGroupsProfile(item);
                                setRoomId(item.id);
                                setOpen(true);
                                fetchChatroomDetails(item.id);
                                fetchMyRoomIdentity(item.id);
                            }} >
                            <Badge size="default">
                                <Avatar shape="square" size="large" src={item.avatar} />
                            </Badge>
                            <List.Item.Meta
                                title={item.name}
                                style={{marginLeft:"10px"}}
                            />
                        </List.Item>
                    )}
                />
                <Button type="primary" style={{ position: "absolute", bottom: 0 }} onClick={handleOpenModal}>
                    <Badge count={invitationList.length}>
                        Handle invitations
                    </Badge>
                </Button>
                <Modal title="Pending Invitations" open={isInvitationListVisible} onCancel={() => setIsInvitationListVisible(false)} footer={null}>
                    <List
                        dataSource={invitationList}
                        renderItem={(item: InvitationDataType) => (
                            <List.Item key={item.invitation_id}>
                                <List.Item.Meta
                                    title={<a>{item.chatroom_name} (Invite {item.invited_username})</a>}
                                    description={`Invited by ${item.inviter_username}`}
                                />
                                <div>Invitation time: {item.create_time}</div>
                                <Button type="primary" onClick={() => handleAccept(item.invitation_id, "accept")}>Accept</Button>
                                <Button danger onClick={() => handleAccept(item.invitation_id, "reject")}>Reject</Button>
                            </List.Item>
                        )}
                    />
                </Modal>
            </Sider>
            <Drawer width={640} placement="right" closable={false} onClose={() => { setOpen(false); }} open={open}>
                <p className="site-description-item-profile-p" style={{ marginBottom: 24, fontWeight: "bold" }}>
                    Group Profile
                </p>
                <Avatar src={GroupsProfile?.avatar} size={64} />
                <Divider />
                <Row>
                <Col span={12}>
                    <DescriptionItem title="Group Name" content={GroupsProfile?.name} />
                </Col>
                <Col span={12}>
                    <DescriptionItem title="My Name" content={ store.getState().auth.name } />
                </Col>
                </Row>
                <Row>
                    <Col span={24}>
                        <DescriptionItem
                            title="Group Owner"
                            content={chatroomDetails?.member.filter(member => member.role === "owner")[0]?.name}
                        />
                    </Col>
                </Row>
                <Divider />
                <Modal title="Friends List" open={isModal1Visible} onCancel={() => setIsModal1Visible(false)} footer={null}>
                    <List
                        dataSource={myFriends}
                        renderItem={item => {
                            const isMemberInChatroom = chatroomDetails?.member.some(member => member.id === item.id);
                            return (
                                <List.Item>
                                    <Button disabled={isMemberInChatroom || item.name === store.getState().auth.name} onClick={() => inviteFriend(item, roomId)}>
                                        {item.name === store.getState().auth.name ? `This is yourself: ${item.name}` : isMemberInChatroom ? `${item.name} is already in the chatroom` : `Invite ${item.name}`}
                                    </Button>
                                </List.Item>
                            );
                        }}
                    />
                </Modal>
                {/*需要修改为群聊成员列表*/}
                <Modal title="Group Member List" open={isModal3Visible} onCancel={() => setIsModal3Visible(false)} footer={null}>
                    <List
                        dataSource={chatroomDetails?.member.filter(member => member.id)}
                        renderItem={item => (
                            <List.Item>
                                <Button disabled={item.role === "admin" || item.name === store.getState().auth.name} onClick={() => manageAdmin(item.id, roomId)}>
                                    {item.name === store.getState().auth.name ? `This is yourself: ${item.name}` : item.role === "admin" ? `Admin: ${item.name}` : `Set to admin ${item.name}`}
                                </Button>
                            </List.Item>
                        )}
                    />
                </Modal>
                {/*需要修改为群聊成员列表*/}
                <Modal title="Group Member List" open={isModal4Visible} onCancel={() => setIsModal4Visible(false)} footer={null}>
                    <List
                        dataSource={chatroomDetails?.member.filter(member => member.id)}
                        renderItem={item => (
                            <List.Item>
                                <Button disabled={item.name === store.getState().auth.name} onClick={() => removeMember(item.id, roomId)}>{item.name === store.getState().auth.name ? `This is yourself: ${item.name}` : `Remove member ${item.name}`}</Button>
                            </List.Item>
                        )}
                    />
                </Modal>
                <Modal title="Group Member List" open={isTransOwnerModalVisible} onCancel={() => setTransOwnerModalVisible(false)} footer={null}>
                    <List
                        dataSource={chatroomDetails?.member.filter(member => member.id)}
                        renderItem={item => (
                            <List.Item>
                                <Button disabled={ item.name === store.getState().auth.name } onClick={() => transOwner(item.id)}> {item.name === store.getState().auth.name? `This is yourself: ${item.name}`: `Transfer Owner ${item.name}`}</Button>
                            </List.Item>
                        )}
                    />
                </Modal>
                <Modal title="Notice Board" open={isNoticeBoardOpen} onCancel={() => setNoticeBoardOpen(false)} footer={null}>
                    <Form
                        onFinish={values => {
                            writeNotice(values.title, values.text, roomId);
                            setNoticeBoardOpen(false);
                        }}
                    >
                        <Form.Item
                            name="title"
                            rules={[{ required: true, message: "Please input your title!" }]}
                        >
                            <Input placeholder="Write your title here" />
                        </Form.Item>
                        <Form.Item
                            name="text"
                            rules={[{ required: true, message: "Please input your text!" }]}
                        >
                            <Input.TextArea placeholder="Write your text here" />
                        </Form.Item>
                        <Form.Item>
                            <Button type="primary" htmlType="submit">
                                Submit
                            </Button>
                        </Form.Item>
                    </Form>
                </Modal>
                <Button
                    type="primary"
                    key={"invite-btn"}
                    style={{ marginRight: "10px" }}
                    onClick={() => {
                        inviteUserList();
                    }}>
                    Invite User
                </Button>
                <Button
                    type="primary"
                    key={"manage-admin-btn"}
                    onClick={() => {
                        if (myRoomIdentity.is_owner || myRoomIdentity.is_admin) {
                            manageAdminList();
                        }
                    }}
                    disabled={!myRoomIdentity.is_owner && !myRoomIdentity.is_admin}
                    style={{ marginRight: "10px", backgroundColor: !myRoomIdentity.is_owner && !myRoomIdentity.is_admin ? "lightgrey" : undefined, borderColor: !myRoomIdentity.is_owner && !myRoomIdentity.is_admin ? "lightgrey" : undefined }}
                >
                    Set Admin
                </Button>
                <Button
                    key={"remove-member-btn"}
                    danger
                    onClick={() => {
                        if (myRoomIdentity.is_owner || myRoomIdentity.is_admin) {
                            removeMemberList();
                        }
                    }}
                    disabled={!myRoomIdentity.is_owner && !myRoomIdentity.is_admin}
                    style={{ marginRight: "10px", backgroundColor: !myRoomIdentity.is_owner && !myRoomIdentity.is_admin ? "lightgrey" : undefined, borderColor: !myRoomIdentity.is_owner && !myRoomIdentity.is_admin ? "lightgrey" : undefined }}
                >
                    Remove Member
                </Button>
                <Button
                    type="primary"
                    danger
                    key={"leave-group-btn"}
                    style={{ marginRight: "10px" }}
                    onClick={() => {
                        leaveGroup();
                    }}>
                    Leave Group
                </Button>
                <Button
                    type="primary"
                    key={"transfer-owner-btn"}
                    onClick={() => {
                        if (myRoomIdentity.is_owner) {
                            transOwnerList();
                        }
                    }}
                    disabled={!myRoomIdentity.is_owner}
                    style={{ marginRight: "10px", backgroundColor: !myRoomIdentity.is_owner ? "lightgrey" : undefined, borderColor: !myRoomIdentity.is_owner ? "lightgrey" : undefined }}
                >
                    Transfer Owner
                </Button>
                <Button
                    type="primary"
                    key={"write-notice-btn"}
                    onClick={() => {
                        if (myRoomIdentity.is_owner || myRoomIdentity.is_admin) {
                            writeNoticeBoard();
                        }
                    }}
                    disabled={!myRoomIdentity.is_owner && !myRoomIdentity.is_admin}
                    style={{ marginRight: "10px", backgroundColor: !myRoomIdentity.is_owner && !myRoomIdentity.is_admin ? "lightgrey" : undefined, borderColor: !myRoomIdentity.is_owner && !myRoomIdentity.is_admin ? "lightgrey" : undefined }}
                >
                    Write Notice
                </Button>
                {chatroomDetails && (
                    <div>
                        <h2>Members</h2>
                        <ul>
                            {chatroomDetails.member.map((member: { id: React.Key | null | undefined; name: string | number | boolean | React.ReactElement<any, string | React.JSXElementConstructor<any>> | Iterable<React.ReactNode> | React.ReactPortal | React.PromiseLikeOfReactNode | null | undefined; }) => (
                                <li key={member.id}>{member.name}</li>
                            ))}
                        </ul>
                        <h2>Notices</h2>
                        <ul>
                            {chatroomDetails.notice.map((notice: { create_time: React.Key | null | undefined; title: string | number | boolean | React.ReactElement<any, string | React.JSXElementConstructor<any>> | Iterable<React.ReactNode> | React.ReactPortal | React.PromiseLikeOfReactNode | null | undefined; text: string | number | boolean | React.ReactElement<any, string | React.JSXElementConstructor<any>> | Iterable<React.ReactNode> | React.ReactPortal | React.PromiseLikeOfReactNode | null | undefined; }) => (
                                <li key={notice.create_time} style={{ border: "1px solid black", padding: "10px", margin: "10px 0" }}>
                                    <h3>{notice.title} <span style={{ fontFamily: "Courier New, monospace" }}>{notice.create_time}</span></h3>
                                    <p>{notice.text}</p>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </Drawer>
        </Layout>
    );
};

export default GroupListPage;