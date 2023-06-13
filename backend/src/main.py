import sys
import time
import threading
import json

sys.path.append("module")
sys.path.append("data")

import pandas as pd
from model import Model
from checker import Checker
from file_generating import UpdateFiles, UpdateLabel, LabelExisting, GenerateContextsData  # type: ignore
from files_path import FILE_CONTEXTS, FILE_PAIRING, FILE_PENDING_DATA
from response import (
    RESPONSE_SUCCESS,
    RESPONSE_INVALID_MODE,
    RESULT_NOT_FOUND,
    RESPONSE_FAILED_TO_UPDATE,
    RESPONSE_DUPLICATE_DATA,
    RESPONSE_INVALID_VALUE,
    RESPONSE_INVALID_DATA,
)

model = Model()


def use_model(res):
    model.initialize(res)
    res = model.classify()

    if res:
        return res
    else:
        return RESULT_NOT_FOUND


def check(target="general"):
    if target == "context":
        return Checker(FILE_CONTEXTS).has_data()
    else:
        return Checker(FILE_PENDING_DATA).has_data()


from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Suggest(BaseModel):
    question: str


class Feedback(BaseModel):
    question: str
    response: str
    label_id: int
    label_name: str
    keywords: list


class Context(BaseModel):
    context: str
    default_label: int


class DataUpdate(BaseModel):
    mode: str
    data: list


class VecMessage(BaseModel):
    sentence: str


@app.post("/suggest")
def post_suggest(suggest: Suggest):
    res = use_model(suggest.question)
    pairing_data = pd.read_json(FILE_PAIRING)
    pairing_data = list(pairing_data["type"])
    res = {"response": [], "label": -1} if res == RESULT_NOT_FOUND else res
    return {"suggestion": res, "labels": pairing_data}


# -1  =>  non-existing label and needed to be updated into the pending-data
@app.post("/feedback")
def post_feedback(feedback: Feedback):
    try:
        if int(feedback.label_id) == -1:
            # Appending to pairing
            lid = UpdateLabel(feedback.label_name)

            if lid != -1:
                # Append to pending-data
                data = {
                    "question": feedback.question,
                    "response": feedback.response,
                    "label": lid,
                }

                pending_data = pd.DataFrame(data, index=range(1))

                pending_data.to_csv(
                    FILE_PENDING_DATA, mode="a", index=False, header=False
                )

                data = None
                with open(FILE_PAIRING, "r") as f:
                    data = json.load(f)

                for i, d in enumerate(data):
                    if i == lid:
                        d["keywords"] = list(set(d["keywords"] + feedback.keywords))
                        d["keywords"] = [d for d in d["keywords"] if d != ""]

                with open(FILE_PAIRING, "w") as f:
                    json.dump(data, f)
            else:
                return {"response": "failed"}

        elif LabelExisting(int(feedback.label_id)):
            data = {
                "question": feedback.question,
                "response": feedback.response,
                "label": feedback.label_id,
            }
            pending_data = pd.DataFrame(data, index=range(1))
            pending_data.to_csv(FILE_PENDING_DATA, mode="a", index=False, header=False)
        else:
            return {"response": "failed to update feedback."}
    except:
        return {"response": "failed"}

    return {"response": "success"}


@app.post("/context")
def post_context(context: Context):
    try:
        data = {"context": context.context, "label": context.default_label}
        df = pd.DataFrame(data, index=[0])
        df.to_csv(FILE_CONTEXTS, mode="a", index=False, header=False)
    except:
        return {"response": "failed"}
    return {"response": "success"}


@app.get("/pending_data")
def get_pending_data():
    pairing_data = pd.read_json(FILE_PAIRING)
    pairing_data = list(pairing_data["type"])
    return {
        "labels_data": pairing_data,
        "pending_data": pd.DataFrame(pd.read_csv(FILE_PENDING_DATA)).values.tolist(),
    }


@app.get("/context_data")
def get_context_data():
    pairing_data = pd.read_json(FILE_PAIRING)
    pairing_data = list(pairing_data["type"])
    return {
        "labels_data": pairing_data,
        "context_data": pd.DataFrame(pd.read_csv(FILE_CONTEXTS)).values.tolist(),
    }


@app.get("/label_data")
def get_labels_data():
    try:
        with open(FILE_PAIRING, "r") as file:
            data = json.load(file)
    except:
        return {"response": "Failed."}
    return {"response": data}


@app.post("/context_data/update")
def post_context_data_update(context_data_update: DataUpdate):
    modes = ["a", "m", "d"]
    if context_data_update.mode in modes:
        context_data = pd.DataFrame(pd.read_csv(FILE_CONTEXTS)).values.tolist()
        new_context_data = []

        if context_data_update.mode == modes[0]:
            try:
                if int(context_data_update.data[1]) == -10:
                    # Appending to pairing
                    lid = UpdateLabel(context_data_update.data[2])

                    if lid != -1:
                        # Append to pending-data
                        data = {
                            "context": context_data_update.data[0],
                            "label": lid,
                        }
                        context_data = pd.DataFrame(data, index=range(1))
                        context_data.to_csv(
                            FILE_CONTEXTS,
                            mode="a",
                            index=False,
                            header=False,
                        )

                elif LabelExisting(int(context_data_update.data[1])):
                    data = {
                        "context": context_data_update.data[0],
                        "label": int(context_data_update.data[1]),
                    }
                    context_data = pd.DataFrame(data, index=range(1))
                    context_data.to_csv(
                        FILE_CONTEXTS,
                        mode="a",
                        index=False,
                        header=False,
                    )
                else:
                    return {"response": "Invalid label detection."}
            except:
                return {"response": "Failed to update data."}

        elif context_data_update.mode == modes[1]:
            c = context_data_update.data[0]
            l = context_data_update.data[1]
            nl = context_data_update.data[2]
            od = context_data_update.data[3]  # [oq, or, ol]

            if l == -10:
                l = UpdateLabel(nl)

            new_context_data = [d if d != od else [c, l] for d in context_data]

            # If DELETE
        elif context_data_update.mode == modes[2]:
            new_context_data = [
                d for d in context_data if d != context_data_update.data
            ]

        if context_data_update.mode == modes[1] or context_data_update.mode == modes[2]:
            new_c = [d[0] for d in new_context_data]
            new_l = [d[1] for d in new_context_data]
            df = pd.DataFrame({"context": new_c, "label": new_l})
            df.to_csv(FILE_CONTEXTS, index=False)

    else:
        return {"response": "Invalid mode."}

    return {"reponse": "success"}


@app.post("/pending_data/update")
def post_pending_data_update(pending_data_update: DataUpdate):
    # mode => "a" add, "m" modify, "d" delete
    modes = ["a", "m", "d"]
    # list => [question, response, label]

    if pending_data_update.mode in modes:
        pending_data = pd.DataFrame(pd.read_csv(FILE_PENDING_DATA)).values.tolist()
        new_pending_data = []

        if pending_data_update.mode == modes[0]:
            try:
                if int(pending_data_update.data[2]) == -10:
                    # Appending to pairing
                    lid = UpdateLabel(pending_data_update.data[3])

                    if lid != -1:
                        # Append to pending-data
                        data = {
                            "question": pending_data_update.data[0],
                            "response": pending_data_update.data[1],
                            "label": lid,
                        }
                        pending_data = pd.DataFrame(data, index=range(1))
                        pending_data.to_csv(
                            FILE_PENDING_DATA,
                            mode="a",
                            index=False,
                            header=False,
                        )

                elif LabelExisting(int(pending_data_update.data[2])):
                    data = {
                        "question": pending_data_update.data[0],
                        "response": pending_data_update.data[1],
                        "label": int(pending_data_update.data[2]),
                    }
                    pending_data = pd.DataFrame(data, index=range(1))
                    pending_data.to_csv(
                        FILE_PENDING_DATA, mode="a", index=False, header=False
                    )
                else:
                    return {"response": "Invalid label detection."}
            except:
                return {"response": "Failed to update data."}

        elif pending_data_update.mode == modes[1]:
            q = pending_data_update.data[0]
            r = pending_data_update.data[1]
            l = pending_data_update.data[2]
            nl = pending_data_update.data[3]
            od = pending_data_update.data[4]  # [oq, or, ol]

            if l == -10:
                l = UpdateLabel(nl)

            new_pending_data = [d if d != od else [q, r, l] for d in pending_data]

        # If DELETE
        elif pending_data_update.mode == modes[2]:
            new_pending_data = [
                d for d in pending_data if d != pending_data_update.data
            ]

        if pending_data_update.mode == modes[1] or pending_data_update.mode == modes[2]:
            new_q = [d[0] for d in new_pending_data]
            new_r = [d[1] for d in new_pending_data]
            new_l = [d[2] for d in new_pending_data]
            df = pd.DataFrame({"question": new_q, "response": new_r, "label": new_l})
            df.to_csv(FILE_PENDING_DATA, index=False)

    else:
        return {"response": "Invalid mode."}

    return {"reponse": "success"}


@app.post("/label_data/update")
def post_label_data_update(labels_data_update: DataUpdate):
    """
    Expected value:

    mode: "a", "m", "d"
    data: OBJECT,  specific label data
        e.g.
            "a":
            {"type": "product", "keywords": ["mathematical_product", "ware", "production", "product", "merchandise", "intersection", "Cartesian_product"]}

            "m" || "d":
            { "label": 11, "type": "product", "keywords": ["mathematical_product", "ware", "production", "product", "merchandise", "intersection", "Cartesian_product"] }

    """

    modes = ["a", "m", "d"]

    if labels_data_update.mode in modes:
        try:
            # Expected labels_data_update.data
            # {
            #    "type": "labels_type"
            #    "keywords" : []
            # }
            labels_data = get_labels_data()["response"]
            labels_type = [d["type"] for d in labels_data]  # type: ignore
            labels_label = [d["label"] for d in labels_data]  # type: ignore

            # APPEND
            # [type, keywords, label]
            if labels_data_update.mode == "a":
                if labels_data_update.data[0] in labels_type:  # type: ignore
                    return RESPONSE_DUPLICATE_DATA

                if type(labels_data_update.data[0]) == str and type(labels_data_update.data[1]) == list and len(labels_data_update.data[1]) > 0:  # type: ignore

                    new_labels_data = labels_data  # type: ignore
                    labels_data_update.data[1].append(labels_data_update.data[0])
                    labels_data_update.data[1] = list(set(labels_data_update.data[1]))
                    new_data = {
                        "label": int(labels_label[-1]) + 1,
                        "type": labels_data_update.data[0],
                        "keywords": labels_data_update.data[1],
                    }
                    new_labels_data.append(new_data)  # type: ignore

                    with open(FILE_PAIRING, "w") as file:
                        json.dump(new_labels_data, file)

                else:
                    return RESPONSE_INVALID_DATA

            elif labels_data_update.mode == "m":

                # labels_data_update.data["label"] : int
                # check if the label id is in the pairing data
                if labels_data_update.data[0] not in labels_label:  # type: ignore
                    new_res = RESPONSE_INVALID_VALUE
                    new_res["value"] = "Invalid label. Not found."
                    return new_res

                new_labels_data = []
                for d in labels_data:
                    if d["label"] == labels_data_update.data[0]:  # type: ignore
                        new_dict = {
                            "label": labels_data_update.data[0],
                            "type": labels_data_update.data[1],
                            "keywords": labels_data_update.data[2],
                        }
                        new_labels_data.append(new_dict)
                    else:
                        new_labels_data.append(d)

                with open(FILE_PAIRING, "w") as file:
                    json.dump(new_labels_data, file)
            else:
                # labels_data_update.data["label"] : int
                # check if the label id is in the pairing data

                if labels_data_update.data[0] not in labels_label:  # type: ignore
                    new_res = RESPONSE_INVALID_VALUE
                    new_res["value"] = "Invalid label. Not found."
                    return new_res

                new_labels_data = [d for d in labels_data if d["label"] != labels_data_update.data[0]]  # type: ignore
                with open(FILE_PAIRING, "w") as file:
                    json.dump(new_labels_data, file)

        except:
            return RESPONSE_FAILED_TO_UPDATE
    else:
        return RESPONSE_INVALID_MODE

    return RESPONSE_SUCCESS


@app.post("/vec/message")
def post_vec_message(vec_message: VecMessage):
    model.initialize(vec_message.sentence)
    return {"response": model.get_vec_sentence()}


def run_app():
    uvicorn.run(
        "main:app", host="127.0.0.1", port=5000, reload=False, log_level="debug"
    )


def process1():
    while True:
        time.sleep(10)  # Sleep for 1 hour
        # Update files once per hour
        check_result = check()
        if check_result:
            vocab = model.get_vocab()
            UpdateFiles(vocab)  # type: ignore # AFTER CHECKING CONTEXTS CLEAR IT
            model.update()
            print("GENERAL UPDATED")


def process2():
    while True:
        time.sleep(60)  # Sleep for 1 min
        # Update files once per hour
        check_result = check("context")
        if check_result:
            # vocab = model.get_vocab()
            GenerateContextsData(model=model)
            print("CONTEXTS UPDATED")


if __name__ == "__main__":
    # Start Process 1 in a separate thread
    t1 = threading.Thread(target=process1)
    t1.start()

    # Start Process 2 in the thread 2
    t2 = threading.Thread(target=process2)
    t2.start()

    # Start Process 3 in the main thread
    run_app()
