import { Command } from "commander";
import axios from "axios";
import {
  Osarc200TokenClient as OSARC200TokenClient,
  APP_SPEC as OSARC200TokenSpec,
} from "./clients/OSARC200TokenClient.js";
import {
  Osarc200TokenFactoryClient as OSARC200TokenFactoryClient,
  APP_SPEC as OSARC200TokenFactorySpec,
} from "./clients/OSARC200TokenFactoryClient.js";

import algosdk, {
  AtomicTransactionComposer,
  makePaymentTxnWithSuggestedParamsFromObject,
  TransactionSigner,
  waitForConfirmation,
} from "algosdk";
import { CONTRACT, abi } from "ulujs";
import moment from "moment";
import * as dotenv from "dotenv";
import BigNumber from "bignumber.js";
import fs from "fs";
import { SendTransactionFrom } from "@algorandfoundation/algokit-utils/types/transaction.js";
dotenv.config({ path: ".env" });

function stripTrailingZeroBytes(str: string) {
  return str.replace(/\0+$/, ""); // Matches one or more '\0' at the end of the string and removes them
}

function padStringWithZeroBytes(input: string, length: number): string {
  const paddingLength = length - input.length;

  if (paddingLength > 0) {
    const zeroBytes = "\0".repeat(paddingLength);
    return input + zeroBytes;
  }

  return input; // Return the original string if it's already long enough
}

function uint8ArrayToBigInt(uint8Array: Uint8Array) {
  let result = BigInt(0); // Initialize the BigInt result
  for (let i = 0; i < uint8Array.length; i++) {
    result = (result << BigInt(8)) + BigInt(uint8Array[i]); // Shift 8 bits and add the current byte
  }
  return result;
}

export const program = new Command();

const { MN } = process.env;

export const acc = algosdk.mnemonicToSecretKey(MN || "");
export const { addr, sk } = acc;

export const addressses = {
  deployer: addr,
};

export const sks = {
  deployer: sk,
};

// TESTNET
// const ALGO_SERVER = "https://testnet-api.voi.nodly.io";
// const ALGO_INDEXER_SERVER = "https://testnet-idx.voi.nodly.io";
// const ARC72_INDEXER_SERVER = "https://arc72-idx.nautilus.sh";

// MAINNET
const ALGO_SERVER = "https://mainnet-api.voi.nodely.dev";
const ALGO_INDEXER_SERVER = "https://mainnet-idx.voi.nodely.dev";
const ARC72_INDEXER_SERVER = "https://mainnet-idx.nautilus.sh";

const algodServerURL = process.env.ALGOD_SERVER || ALGO_SERVER;
const algodClient = new algosdk.Algodv2(
  process.env.ALGOD_TOKEN || "",
  algodServerURL,
  process.env.ALGOD_PORT || ""
);

const indexerServerURL = process.env.INDEXER_SERVER || ALGO_INDEXER_SERVER;
const indexerClient = new algosdk.Indexer(
  process.env.INDEXER_TOKEN || "",
  indexerServerURL,
  process.env.INDEXER_PORT || ""
);

const arc72IndexerURL =
  process.env.ARC72_INDEXER_SERVER || ARC72_INDEXER_SERVER;

const makeSpec = (methods: any) => {
  return {
    name: "",
    desc: "",
    methods,
    events: [],
  };
};

const signSendAndConfirm = async (txns: string[], sk: any) => {
  const stxns = txns
    .map((t) => new Uint8Array(Buffer.from(t, "base64")))
    .map(algosdk.decodeUnsignedTransaction)
    .map((t: any) => algosdk.signTransaction(t, sk));
  await algodClient.sendRawTransaction(stxns.map((txn: any) => txn.blob)).do();
  return await Promise.all(
    stxns.map((res: any) =>
      algosdk.waitForConfirmation(algodClient, res.txID, 4)
    )
  );
};

type DeployType = "osarc200-token" | "factory-osarc200-token";

interface DeployOptions {
  type: DeployType;
  name: string;
  debug?: boolean;
}

export const deploy: any = async (options: DeployOptions) => {
  if (options.debug) {
    console.log(options);
  }
  const deployer = {
    addr: addr,
    sk: sk,
  };
  let Client;
  switch (options.type) {
    case "factory-osarc200-token": {
      Client = OSARC200TokenFactoryClient;
      break;
    }
    case "osarc200-token": {
      Client = OSARC200TokenClient;
      break;
    }
  }
  const clientParams: any = {
    resolveBy: "creatorAndName",
    findExistingUsing: indexerClient,
    creatorAddress: deployer.addr,
    name: options.name || "",
    sender: deployer,
  };
  const appClient = Client ? new Client(clientParams, algodClient) : null;
  if (appClient) {
    const app = await appClient.deploy({
      deployTimeParams: {},
      onUpdate: "update",
      onSchemaBreak: "fail",
    });
    return app.appId;
  }
};
program
  .command("deploy")
  .requiredOption("-t, --type <string>", "Specify factory type")
  .requiredOption("-n, --name <string>", "Specify contract name")
  .option("--debug", "Debug the deployment", false)
  .description("Deploy a specific contract type")
  .action(async (options: DeployOptions) => {
    const apid = await deploy(options);
    if (!apid) {
      console.log("Failed to deploy contract");
      return;
    }
    console.log(apid);
  });

const factory = new Command("factory").description(
  "Manage arc200 token factory"
);

interface FactoryCreateOptions {
  apid: number;

  debug?: boolean;
  simulate?: boolean;
}

export const factoryCreate: any = async (options: FactoryCreateOptions) => {
  if (options.debug) {
    console.log(options);
  }
  const ci = new CONTRACT(
    Number(options.apid),
    algodClient,
    indexerClient,
    makeSpec(OSARC200TokenFactorySpec.contract.methods),
    {
      addr,
      sk: new Uint8Array(0),
    }
  );
  ci.setPaymentAmount(1152300);
  ci.setFee(4000);
  const createR = await ci.create();
  if (options.debug) {
    console.log(createR);
  }
  if (createR.success) {
    if (!options.simulate) {
      await signSendAndConfirm(createR.txns, sk);
    }
    return Number(createR.returnValue);
  }
  return 0;
};

factory
  .command("create")
  .description("Create a new arc200 token")
  .requiredOption("-a, --apid <number>", "Specify the application ID")
  .option("--debug", "Debug the deployment", false)
  .option("-r, --simulate", "Simulate the deployment", false)
  .action(async (options: FactoryCreateOptions) => {
    const apid = await factoryCreate({
      ...options,
    });
    console.log("apid:", apid);
  });

const arc200 = new Command("arc200").description("Manage arc200 token");

interface ARC200GlobalStateOptions {
  apid: number;
  lazy?: boolean;
}
export const arc200GetState: any = async (
  options: ARC200GlobalStateOptions
) => {
  const globalState = await new OSARC200TokenClient(
    { resolveBy: "id", id: Number(options.apid) },
    algodClient
  ).getGlobalState();
  if (options.lazy) {
    return { globalState };
  }
  const state = {
    contractVersion: globalState.contractVersion?.asNumber(),
    deploymentVersion: globalState.deploymentVersion?.asNumber(),
    owner: algosdk.encodeAddress(
      globalState.owner?.asByteArray() || new Uint8Array()
    ),
    updatable: globalState.updatable?.asNumber(),
    upgrader: algosdk.encodeAddress(
      globalState.upgrader?.asByteArray() || new Uint8Array()
    ),
    name: stripTrailingZeroBytes(globalState.name?.asString() || ""),
    symbol: stripTrailingZeroBytes(globalState.symbol?.asString() || ""),
    totalSupply: uint8ArrayToBigInt(
      globalState.totalSupply?.asByteArray() || new Uint8Array()
    ).toString(),
    decimals: globalState.decimals?.asNumber(),
  };
  return state;
};
arc200
  .command("get")
  .description("Get the state of the arc200 token")
  .requiredOption("-a, --apid <number>", "Specify the application ID")
  .action(async (options: ARC200GlobalStateOptions) => {
    const globalState = await arc200GetState(options);
    console.log({ globalState });
    return globalState;
  });

//             _       _
//   _ __ ___ (_)_ __ | |_
//  | '_ ` _ \| | '_ \| __|
//  | | | | | | | | | | |_
//  |_| |_| |_|_|_| |_|\__|
//

interface ARC200MintOptions {
  apid: number;
  recipient: string;
  name: string;
  symbol: string;
  totalSupply: number;
  decimals: number;
  sender?: string;
  sk?: any;
  simulate?: boolean;
  debug?: boolean;
}
export const arc200Mint: any = async (options: ARC200MintOptions) => {
  if (options.debug) {
    console.log(options);
    const globalState = await new OSARC200TokenClient(
      { resolveBy: "id", id: Number(options.apid) },
      algodClient
    ).getGlobalState();

    console.log("globalState", globalState);
  }
  const ci = new CONTRACT(
    Number(options.apid),
    algodClient,
    indexerClient,
    makeSpec(OSARC200TokenSpec.contract.methods),
    {
      addr: options.sender || addr,
      sk: options.sk || sk,
    }
  );
  ci.setFee(2000);
  ci.setPaymentAmount(1e6);
  const mintR = await ci.mint(
    options.recipient,
    options.name,
    options.symbol,
    options.decimals,
    options.totalSupply
  );
  if (options.debug) {
    console.log(mintR);
  }
  if (mintR.success) {
    if (!options.simulate) {
      await signSendAndConfirm(mintR.txns, options.sk || sk);
    }
    return true;
  }
  return false;
};
arc200
  .command("mint")
  .description("Get the state of the arc200 token")
  .requiredOption("-a, --apid <number>", "Specify the application ID")
  .requiredOption("-r, --recipient <string>", "Specify the recipient address")
  .requiredOption("-n, --name <string>", "Specify the name")
  .requiredOption("-s, --symbol <string>", "Specify the symbol")
  .requiredOption("-t, --total-supply <number>", "Specify the total supply")
  .requiredOption("-d, --decimals <number>", "Specify the decimals")
  .option("-v, --simulate", "Simulate the mint", false)
  .option("--debug", "Debug the deployment", false)
  .action(async (options) => {
    const success = await arc200Mint({
      ...options,
      //recipient: algosdk.decodeAddress(options.recipient).publicKey,
      name: new Uint8Array(
        Buffer.from(padStringWithZeroBytes(options.name, 32), "utf8")
      ),
      symbol: new Uint8Array(
        Buffer.from(padStringWithZeroBytes(options.symbol, 8), "utf8")
      ),
      decimals: Number(options.decimals),
      totalSupply: BigInt(
        new BigNumber(options.totalSupply)
          .multipliedBy(10 ** options.decimals)
          .toFixed(0)
      ),
    });
    console.log("Mint success:", success);
  });

//  _           _
// | |__   __ _| | __ _ _ __   ___ ___
// | '_ \ / _` | |/ _` | '_ \ / __/ _ \
// | |_) | (_| | | (_| | | | | (_|  __/
// |_.__/ \__,_|_|\__,_|_| |_|\___\___|
//

interface ARC200BalanceOfOptions {
  apid: number;
  owner: string;
}

export const arc200BalanceOf: any = async (options: ARC200BalanceOfOptions) => {
  const owner = options.owner || addr;
  const ci = new CONTRACT(
    Number(options.apid),
    algodClient,
    indexerClient,
    makeSpec(OSARC200TokenSpec.contract.methods),
    {
      addr: owner,
      sk: new Uint8Array(0),
    }
  );
  const balanceR = (await ci.arc200_balanceOf(owner)).returnValue;
  return balanceR.toString();
};

arc200
  .command("balance")
  .description("Get the balance of the arc200 token")
  .requiredOption("-a, --apid <number>", "Specify the application ID")
  .option("-o, --owner <string>", "Specify the owner address")
  .action(async (options) => {
    const balance = await arc200BalanceOf(options);
    console.log(balance);
  });

//        _ _
//   __ _| | | _____      ____ _ _ __   ___ ___
//  / _` | | |/ _ \ \ /\ / / _` | '_ \ / __/ _ \
// | (_| | | | (_) \ V  V / (_| | | | | (_|  __/
//  \__,_|_|_|\___/ \_/\_/ \__,_|_| |_|\___\___|
//

interface ARC200AllowanceOptions {
  apid: number;
  owner: string;
  spender: string;
}

export const arc200Allowance: any = async (options: ARC200AllowanceOptions) => {
  const owner = options.owner || addr;
  const spender = options.spender || addr;
  const ci = new CONTRACT(
    Number(options.apid),
    algodClient,
    indexerClient,
    makeSpec(OSARC200TokenSpec.contract.methods),
    {
      addr: owner,
      sk: new Uint8Array(0),
    }
  );
  const allowanceR = await ci.arc200_allowance(owner, spender);
  return allowanceR;
};

arc200
  .command("allowance")
  .description("Get the allowance of the arc200 token")
  .requiredOption("-a, --apid <number>", "Specify the application ID")
  .option("-o, --owner <string>", "Specify the owner address")
  .option("-s, --spender <string>", "Specify the spender address")
  .action(async (options) => {
    const allowance = (await arc200Allowance(options)).returnValue.toString();
    console.log(allowance);
  });

//
//   __ _ _ __  _ __  _ __ _____   _____
//  / _` | '_ \| '_ \| '__/ _ \ \ / / _ \
// | (_| | |_) | |_) | | | (_) \ V /  __/
//  \__,_| .__/| .__/|_|  \___/ \_/ \___|
//       |_|   |_|
//

interface ARC200ApproveOptions {
  apid: number;
  spender: string;
  amount: number;
  simulate?: boolean;
  debug?: boolean;
}

export const arc200Approve: any = async (options: ARC200ApproveOptions) => {
  const ci = new CONTRACT(
    Number(options.apid),
    algodClient,
    indexerClient,
    makeSpec(OSARC200TokenSpec.contract.methods),
    {
      addr: addr,
      sk: sk,
    }
  );
  ci.setPaymentAmount(28500 + 3500);
  const approveR = await ci.arc200_approve(options.spender, options.amount);
  if (options.debug) {
    console.log(approveR);
  }
  if (approveR.success) {
    if (!options.simulate) {
      await signSendAndConfirm(approveR.txns, sk);
    }
    return true;
  }
  return false;
};

arc200
  .command("approve")
  .description("Approve the arc200 token")
  .requiredOption("-a, --apid <number>", "Specify the application ID")
  .requiredOption("-s, --spender <string>", "Specify the spender address")
  .requiredOption("-m, --amount <number>", "Specify the amount")
  .option("-t, --simulate", "Simulate the approval", false)
  .option("--debug", "Debug the deployment", false)
  .action(async (options) => {
    const success = await arc200Approve({
      ...options,
      amount: BigInt(options.amount),
    });
    console.log("Approve success:", success);
  });

//  _                        __
// | |_ _ __ __ _ _ __  ___ / _| ___ _ __
// | __| '__/ _` | '_ \/ __| |_ / _ \ '__|
// | |_| | | (_| | | | \__ \  _|  __/ |
//  \__|_|  \__,_|_| |_|___/_|  \___|_|
//

interface ARC200TransferOptions {
  apid: number;
  receiver: string;
  amount: number;
  simulate?: boolean;
  debug?: boolean;
}

export const arc200Transfer: any = async (options: ARC200TransferOptions) => {
  const ci = new CONTRACT(
    Number(options.apid),
    algodClient,
    indexerClient,
    makeSpec(OSARC200TokenSpec.contract.methods),
    {
      addr: addr,
      sk: sk,
    }
  );
  ci.setPaymentAmount(28500);
  const transferR = await ci.arc200_transfer(options.receiver, options.amount);
  if (options.debug) {
    console.log(transferR);
  }
  if (transferR.success) {
    if (!options.simulate) {
      await signSendAndConfirm(transferR.txns, sk);
    }
    return true;
  }
  return false;
};

arc200
  .command("transfer")
  .description("Transfer the arc200 token")
  .requiredOption("-a, --apid <number>", "Specify the application ID")
  .requiredOption("-r, --receiver <string>", "Specify the receiver address")
  .requiredOption("-m, --amount <number>", "Specify the amount")
  .option("-s, --simulate", "Simulate the transfer", false)
  .option("--debug", "Debug the deployment", false)
  .action(async (options) => {
    const success = await arc200Transfer({
      ...options,
      amount: BigInt(options.amount),
    });
    console.log("Transfer success:", success);
  });

//                   _       _
//   _   _ _ __   __| | __ _| |_ ___
//  | | | | '_ \ / _` |/ _` | __/ _ \
//  | |_| | |_) | (_| | (_| | ||  __/
//   \__,_| .__/ \__,_|\__,_|\__\___|
//        |_|
//

arc200
  .command("update")
  .description("Update the arc200 token")
  .requiredOption("-a, --apid <number>", "Specify the application ID")
  .option("-s, --simulate", "Simulate the update", false)
  .option("--debug", "Debug the deployment", false)
  .action(async (options) => {
    if (options.debug) {
      console.log("options", options);
    }
    const apid = Number(options.apid);
    const res = await new OSARC200TokenClient(
      {
        resolveBy: "id",
        id: apid,
        sender: {
          addr,
          sk,
        },
      },
      algodClient
    ).appClient.update();
    if (options.debug) {
      console.log(res);
    }
  });

//  _    _ _ _
// | | _(_) | |
// | |/ / | | |
// |   <| | | |
// |_|\_\_|_|_|
//

interface ARC200KillOptions {
  apid: number;
  simulate?: boolean;
  debug?: boolean;
}

export const arc200Kill: any = async (options: ARC200KillOptions) => {
  const ci = new CONTRACT(
    Number(options.apid),
    algodClient,
    indexerClient,
    makeSpec(OSARC200TokenSpec.contract.methods),
    {
      addr: addr,
      sk: sk,
    }
  );
  ci.setFee(3000);
  ci.setOnComplete(5); // deleteApplicationOC
  const killR = await ci.kill();
  if (options.debug) {
    console.log(killR);
  }
  if (killR.success) {
    if (!options.simulate) {
      await signSendAndConfirm(killR.txns, sk);
    }
    return true;
  }
  return false;
};

arc200
  .command("kill")
  .description("Kill the arc200 token")
  .requiredOption("-a, --apid <number>", "Specify the application ID")
  .option("-s, --simulate", "Simulate the kill", false)
  .option("--debug", "Debug the deployment", false)
  .action(async (options) => {
    const success = await arc200Kill(options);
    console.log("Kill success:", success);
  });

program.addCommand(arc200);
program.addCommand(factory);
