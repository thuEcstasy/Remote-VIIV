import { BOARD_LENGTH } from "../constants/constants";
import { stepBoard } from "../utils/logic";
import { Board } from "../utils/types";

const stepBoardGT = (board: Board): Board => {
    const newBoard: Board = [];

    for (let i = 0; i < BOARD_LENGTH; ++i) {
        newBoard.push([]);

        for (let j = 0; j < BOARD_LENGTH; ++j) {
            let aliveCounter = 0;

            const left = (j - 1 + BOARD_LENGTH) % BOARD_LENGTH;
            const right = (j + 1) % BOARD_LENGTH;
            const up = (i - 1 + BOARD_LENGTH) % BOARD_LENGTH;
            const down = (i + 1) % BOARD_LENGTH;
            const checkList = [
                [up, left], [up, j], [up, right],
                [i, left], [i, right],
                [down, left], [down, j], [down, right],
            ];

            checkList.forEach((ord) => {
                if (board[ord[0]][ord[1]] === 1) {
                    ++aliveCounter;
                }
            });

            const nowState = board[i][j];
            if (nowState === 0) {
                if (aliveCounter === 3) {
                    newBoard[i].push(1);
                }
                else {
                    newBoard[i].push(0);
                }
            }
            else {
                if (aliveCounter === 2 || aliveCounter === 3) {
                    newBoard[i].push(1);
                }
                else {
                    newBoard[i].push(0);
                }
            }
        }
    }

    return newBoard;
};

const boardEqual = (a: Board, b: Board): boolean => {
    for (let i = 0; i < BOARD_LENGTH; ++i) {
        for (let j = 0; j < BOARD_LENGTH; ++j) {
            if (a[i][j] !== b[i][j]) {
                return false;
            }
        }
    }

    return true;
};

const TEST_TIMES = 10;
const ITERATION_DEPTH = 5;

it("[Step 1] Game logic test (Step board)", () => {
    for (let test = 0; test < TEST_TIMES; ++test) {
        const initBoard: Board = [];
        for (let i = 0; i < BOARD_LENGTH; ++i) {
            initBoard.push([]);

            for (let j = 0; j < BOARD_LENGTH; ++j) {
                initBoard[i].push(Math.random() < 0.5 ? 0 : 1);
            }
        }

        let testBoard = stepBoard(initBoard);
        let gtBoard = stepBoardGT(initBoard);
        for (let it = 0; it < ITERATION_DEPTH; ++it) {
            // Check size
            expect(testBoard.length).toEqual(BOARD_LENGTH);
            testBoard.forEach((val) => expect(val.length).toEqual(BOARD_LENGTH));

            // Check equality
            expect(boardEqual(testBoard, gtBoard)).toBeTruthy();

            // If the test above passed, here testBoard === gtBoard
            testBoard = stepBoard(testBoard);
            gtBoard = stepBoardGT(gtBoard);
        }
    }
});