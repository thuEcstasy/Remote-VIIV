import { BOARD_LENGTH } from "../constants/constants";
import { getBlankBoard, flipCell } from "../utils/logic";
import { Board } from "../utils/types";

const TEST_TIMES = 10;

it("[Step 3] Flip cell test", () => {
    for (let test = 0; test < TEST_TIMES; ++test) {
        const initBoard: Board = [];
        for (let i = 0; i < BOARD_LENGTH; ++i) {
            initBoard.push([]);

            for (let j = 0; j < BOARD_LENGTH; ++j) {
                initBoard[i].push(Math.random() < 0.5 ? 0 : 1);
            }
        }

        const iConst = Math.floor(Math.random() * BOARD_LENGTH);
        const jConst = Math.floor(Math.random() * BOARD_LENGTH);
        let flippedBoard: Board = getBlankBoard();
        try {
            flippedBoard = flipCell(initBoard, iConst, jConst);
        }
        catch {
            expect(false).toBeTruthy();
        }

        expect(Object.is(initBoard, flippedBoard)).toBeFalsy();
        expect(flippedBoard.length).toEqual(BOARD_LENGTH);
        for (let i = 0; i < BOARD_LENGTH; ++i) {
            expect(flippedBoard[i].length).toEqual(BOARD_LENGTH);

            for (let j = 0; j < BOARD_LENGTH; ++j) {
                if (i === iConst && j === jConst) {
                    expect(initBoard[i][j] === flippedBoard[i][j]).toBeFalsy();
                }
                else {
                    expect(initBoard[i][j] === flippedBoard[i][j]).toBeTruthy();
                }
            }
        }
    }
});