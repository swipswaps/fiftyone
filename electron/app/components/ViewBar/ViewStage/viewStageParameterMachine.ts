import { Machine, actions, sendParent, send } from "xstate";
import viewStageMachine from "./viewStageMachine";
const { assign, choose } = actions;

/**
 * See https://stackoverflow.com/questions/175739/built-in-way-in-javascript-to-check-if-a-string-is-a-valid-number
 * for details about numbers and javascript
 */
const PARSER = {
  bool: {
    parse: (value) =>
      value.toLowerCase().charAt(0).toUpperCase() +
      value.toLowerCase().slice(1),
    validate: (value) => ["true", "false"].indexOf(value.toLowerCase()) >= 0,
  },
  float: {
    parse: (value) => {
      const stripped = value.replace(/[\s]/g, "");
      const [integer, fractional] = stripped.split(".");
      return integer.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + fractional;
    },
    validate: (value) => {
      const stripped = value.replace(/[\s]/g, "");
      return stripped !== "" && !isNaN(+stripped);
    },
  },
  int: {
    parse: (value) =>
      value.replace(/[,\s]/g, "").replace(/\B(?=(\d{3})+(?!\d))/g, ","),
    validate: (value) => /^\d+$/.test(value.replace(/[,\s]/g, "")),
  },
  list: {
    parse: (value) => value,
    validate: (value) => true,
  },
  str: {
    parse: (value) => value,
    validate: (value) => true,
  },
  any: {
    parse: (value) => value,
    validate: (value) => true,
  },
};

export default Machine(
  {
    id: "viewStageParameter",
    initial: "decide",
    context: {
      id: undefined,
      parameter: undefined,
      stage: undefined,
      type: undefined,
      value: undefined,
      submitted: undefined,
      tail: undefined,
      focusOnInit: undefined,
    },
    states: {
      decide: {
        always: [
          {
            target: "editing",
            cond: (ctx) => ctx.focusOnInit,
          },
          {
            target: "reading.submitted",
            cond: (ctx) => ctx.submitted,
          },
          {
            target: "reading.pending",
          },
        ],
      },
      reading: {
        initial: "pending",
        entry: "blurInput",
        states: {
          pending: {},
          submitted: {},
        },
        on: {
          EDIT: "editing",
          BLUR: [
            {
              target: ".pending",
              cond: (ctx) => !ctx.submitted && ctx.prevValue !== "",
              actions: [
                assign({
                  value: ({ prevValue }) => prevValue,
                }),
              ],
            },
            {
              target: ".pending",
              cond: (ctx) => !ctx.submitted && ctx.prevValue === "",
              actions: sendParent("STAGE.DELETE"),
            },
            {
              target: ".submitted",
              cond: (ctx) => ctx.submitted,
            },
          ],
        },
      },
      editing: {
        entry: [
          assign({
            prevValue: (ctx) => ctx.value,
            focusOnInit: false,
          }),
          "focusInput",
        ],
        on: {
          CHANGE: {
            actions: [
              assign({
                value: (ctx, e) => e.value,
              }),
            ],
          },
          COMMIT: [
            {
              target: "decide",
              actions: [
                assign({
                  submitted: true,
                  value: ({ type, value }) =>
                    PARSER[Array.isArray(type) ? type[0] : type].parse(value),
                }),
                sendParent((ctx) => ({
                  type: "PARAMETER.COMMIT",
                  parameter: ctx,
                })),
              ],
              cond: ({ type, value }) =>
                PARSER[Array.isArray(type) ? type[0] : type].validate(value),
            },
            {
              target: "decide",
              actions: assign({
                value: ({ prevValue }) => prevValue,
              }),
            },
          ],
          CANCEL: {
            target: "reading",
            actions: [
              assign({
                value: (ctx) => ctx.prevValue,
              }),
            ],
          },
        },
      },
    },
  },
  {
    actions: {
      blurInput: () => {},
      focusInput: () => {},
    },
  }
);
