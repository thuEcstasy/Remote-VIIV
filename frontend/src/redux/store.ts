import { configureStore } from "@reduxjs/toolkit";
import { combineReducers } from "redux";
import { persistStore, persistReducer } from "redux-persist";
import storage from "redux-persist/lib/storage"; // defaults to localStorage for web
// import AsyncStorage from "@react-native-community/async-storage";
// import AsyncStorage from "@react-native-async-storage/async-storage";

import authReducer from "./auth";
import boardReducer from "./board";

// 合并多个 reducer
const rootReducer = combineReducers({
    auth: authReducer,
    board: boardReducer,
});

// 配置持久化
const persistConfig = {
    key: "root",
    storage,
    whitelist: ["auth", "board"], // 只持久化这两个 reducer 的状态
};

// 创建持久化的 reducer
const persistedReducer = persistReducer(persistConfig, rootReducer);

// 使用持久化的 reducer 创建 store
const store = configureStore({
    reducer: persistedReducer,
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware({
            serializableCheck: {
                ignoredActions: ["persist/PERSIST"],
            },
        }),
});

// 创建 persistor
export const persistor = persistStore(store);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export default store;