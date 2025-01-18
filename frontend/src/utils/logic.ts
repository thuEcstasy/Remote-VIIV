import { BOARD_LENGTH } from "../constants/constants";
import { Board } from "./types";

export const getBlankBoard = (): Board => Array.from(
    { length: BOARD_LENGTH },
    () => Array<0>(BOARD_LENGTH).fill(0),
);

export const boardToString = (board: Board): string => {
    return board.map((row) => row.join("")).join("");
};

export const stringToBoard = (str: string): Board => {
    if (str.length !== BOARD_LENGTH * BOARD_LENGTH) {
        throw new Error("Invalid parameter");
    }

    const board: Board = [];
    for (let i = 0; i < BOARD_LENGTH; ++i) {
        const row: (0 | 1)[] = [];
        for (let j = 0; j < BOARD_LENGTH; ++j) {
            const val = Number(str[i * BOARD_LENGTH + j]);
            if (val !== 0 && val !== 1) {
                return getBlankBoard();
            }

            row.push(val);
        }

        board.push(row);
    }

    return board;
};

export const stepBoard = (board: Board): Board => {
    const newBoard: Board = [];

    /**
     * @todo [Step 1] 请在下面两条注释之间的区域填写你的代码完成该游戏的核心逻辑
     * @note 你可以使用命令 yarn test step 来运行我们编写的单元测试与我们提供的参考实现对拍
     */
    // Step 1 BEGIN
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
    // Step 1 END

    return newBoard;
};

export const flipCell = (board: Board, i: number, j: number): Board => {
    /**
     * @todo [Step 3] 请在下面两条注释之间的区域填写你的代码完成切换细胞状态的任务
     * @note 你可以使用命令 yarn test flip 来运行我们编写的单元测试以检验自己的实现
     */
    // Step 3 BEGIN
    const newBoard = board.map(row => row.slice());
    newBoard[i][j] = newBoard[i][j] ? 0 : 1;
    return newBoard;
    // Step 3 END

    /**
     * @note 该 return 语句是为了在填入缺失代码前也不至于触发 ESLint Error
     */
    throw new Error("This line should be unreachable.");
    return board;
};
