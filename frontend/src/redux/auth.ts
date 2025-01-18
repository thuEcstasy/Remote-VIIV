import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface AuthState {
    token: string;
    name: string;
    email: string;
    phone: string;
    avatar: string;
    id: number;
}

const initialState: AuthState = {
    token: "",
    name: "",
    email: "",
    phone: "",
    avatar: "",
    id: 0,
};

export const authSlice = createSlice({
    name: "auth",
    initialState,
    reducers: {
        setToken: (state, action: PayloadAction<string>) => {
            state.token = action.payload;
        },
        setName: (state, action: PayloadAction<string>) => {
            state.name = action.payload;
        },
        setEmail: (state, action: PayloadAction<string>) => {
            state.email = action.payload;
        },
        setPhone: (state, action: PayloadAction<string>) => {
            state.phone = action.payload;
        },
        setAvatar: (state, action: PayloadAction<string>) => {
            state.avatar = action.payload;
        },
        setId: (state, action: PayloadAction<number>) => {
            state.id = action.payload;
        },
        resetAuth: (state) => {
            state.token = "";
            state.name = "";
        },
    },
});

export const { setToken, setName, setEmail, setPhone, setAvatar, resetAuth, setId } = authSlice.actions;
export default authSlice.reducer;
