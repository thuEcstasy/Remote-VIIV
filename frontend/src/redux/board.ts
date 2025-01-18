import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { Board } from "../utils/types";
import { getBlankBoard } from "../utils/logic";

interface BoardState {
    board: Board;
}

const initialState: BoardState = {
    board: getBlankBoard(),
};

export const boardSlice = createSlice({
    name: "board",
    initialState,
    reducers: {
        setBoardCache: (state, action: PayloadAction<Board>) => {
            state.board = action.payload;
        },
        resetBoardCache: (state) => {
            state.board = getBlankBoard();
        },
    },
});

export const { setBoardCache, resetBoardCache } = boardSlice.actions;
export default boardSlice.reducer;
