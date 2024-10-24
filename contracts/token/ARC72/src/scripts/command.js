import { Command } from "commander";
import { APP_SPEC as OSARC200TokenSpec, } from "./clients/OSARC200TokenClient.js";
import { APP_SPEC as OwnableSpec, } from "./clients/OwnableClient.js";
import { Osarc72TokenClient as OSARC72TokenClient, APP_SPEC as OSARC72TokenSpec, } from "./clients/OSARC72TokenClient.js";
import algosdk from "algosdk";
import { CONTRACT, abi } from "ulujs";
import * as dotenv from "dotenv";
dotenv.config({ path: ".env" });
function stripTrailingZeroBytes(str) {
    return str.replace(/\0+$/, ""); // Matches one or more '\0' at the end of the string and removes them
}
function padStringWithZeroBytes(input, length) {
    const paddingLength = length - input.length;
    if (paddingLength > 0) {
        const zeroBytes = "\0".repeat(paddingLength);
        return input + zeroBytes;
    }
    return input; // Return the original string if it's already long enough
}
function uint8ArrayToBigInt(uint8Array) {
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
const algodClient = new algosdk.Algodv2(process.env.ALGOD_TOKEN || "", algodServerURL, process.env.ALGOD_PORT || "");
const indexerServerURL = process.env.INDEXER_SERVER || ALGO_INDEXER_SERVER;
const indexerClient = new algosdk.Indexer(process.env.INDEXER_TOKEN || "", indexerServerURL, process.env.INDEXER_PORT || "");
// const boxes = [
//   { name: "YXJjNzJfdG9rZW5VUkk=" },
//   { name: "aG9sZGVyX2RhdGE22SB/rskTMQiNckaxpV+g/k0ro2i+WpxNdX5No4Od5g==" },
//   { name: "aG9sZGVyX2RhdGGM1Wvssxtag7AWOrshvUfdYvfb7pdyuzfRLlwy/JrWHA==" },
//   { name: "bmZ0X2RhdGEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQ==" },
//   { name: "bmZ0X2luZGV4AQ==" },
//   { name: "bmZ0X2luZGV4Ag==" },
//   { name: "bmZ0X2luZGV4Aw==" },
//   { name: "bmZ0X2luZGV4BA==" },
//   { name: "bmZ0X2luZGV4BQ==" },
//   { name: "bmZ0X2luZGV4Bg==" },
//   { name: "bmZ0X2luZGV4Bw==" },
//   { name: "bmZ0X2luZGV4CA==" },
//   { name: "bmZ0X2luZGV4CQ==" },
//   { name: "bmZ0X2luZGV4Cg==" },
//   { name: "bmZ0X2luZGV4Cw==" },
//   { name: "bmZ0X2luZGV4DA==" },
//   { name: "bmZ0X2luZGV4DQ==" },
// ];
// for await (const box of boxes) {
//   const { name: boxName } = box;
//   const boxNameB64 = Buffer.from(boxName, "base64").toString("utf8");
//   const boxResponse = await indexerClient
//     .lookupApplicationBoxByIDandName(
//       421076,
//       new Uint8Array(Buffer.from(boxName, "base64"))
//     )
//     .do();
//   const boxValue = boxResponse.value;
//   console.log(boxName, boxNameB64, boxValue);
// }
// process.exit(0);
const arc72IndexerURL = process.env.ARC72_INDEXER_SERVER || ARC72_INDEXER_SERVER;
const makeSpec = (methods) => {
    return {
        name: "",
        desc: "",
        methods,
        events: [],
    };
};
const signSendAndConfirm = async (txns, sk) => {
    const stxns = txns
        .map((t) => new Uint8Array(Buffer.from(t, "base64")))
        .map(algosdk.decodeUnsignedTransaction)
        .map((t) => algosdk.signTransaction(t, sk));
    await algodClient.sendRawTransaction(stxns.map((txn) => txn.blob)).do();
    return await Promise.all(stxns.map((res) => algosdk.waitForConfirmation(algodClient, res.txID, 4)));
};
export const deploy = async (options) => {
    if (options.debug) {
        console.log(options);
    }
    const deployer = {
        addr: addr,
        sk: sk,
    };
    let Client;
    switch (options.type) {
        case "osarc72-token": {
            Client = OSARC72TokenClient;
            break;
        }
        default: {
            console.log("Invalid type");
            return;
        }
    }
    const clientParams = {
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
    .action(async (options) => {
    const apid = await deploy(options);
    if (!apid) {
        console.log("Failed to deploy contract");
        return;
    }
    console.log(apid);
});
// const factory = new Command("factory").description(
//   "Manage arc200 token factory"
// );
// interface FactoryCreateOptions {
//   apid: number;
//   debug?: boolean;
//   simulate?: boolean;
// }
// export const factoryCreate: any = async (options: FactoryCreateOptions) => {
//   if (options.debug) {
//     console.log(options);
//   }
//   const ci = new CONTRACT(
//     Number(options.apid),
//     algodClient,
//     indexerClient,
//     makeSpec(OSARC200TokenFactorySpec.contract.methods),
//     {
//       addr,
//       sk: new Uint8Array(0),
//     }
//   );
//   ci.setPaymentAmount(1152300);
//   ci.setFee(4000);
//   const createR = await ci.create();
//   if (options.debug) {
//     console.log(createR);
//   }
//   if (createR.success) {
//     if (!options.simulate) {
//       await signSendAndConfirm(createR.txns, sk);
//     }
//     return Number(createR.returnValue);
//   }
//   return 0;
// };
// factory
//   .command("create")
//   .description("Create a new arc200 token")
//   .requiredOption("-a, --apid <number>", "Specify the application ID")
//   .option("--debug", "Debug the deployment", false)
//   .option("-r, --simulate", "Simulate the deployment", false)
//   .action(async (options: FactoryCreateOptions) => {
//     const apid = await factoryCreate({
//       ...options,
//     });
//     console.log("apid:", apid);
//   });
const arc72 = new Command("arc72").description("Manage arc72 token");
export const arc72GetState = async (options) => {
    const globalState = await new OSARC72TokenClient({ resolveBy: "id", id: Number(options.apid) }, algodClient).getGlobalState();
    if (options.lazy) {
        return { globalState };
    }
    const state = {
        totalSupply: uint8ArrayToBigInt(globalState.totalSupply?.asByteArray() || new Uint8Array()).toString(),
    };
    return state;
};
arc72
    .command("get")
    .description("Get the state of the arc72 token")
    .requiredOption("-a, --apid <number>", "Specify the application ID")
    .action(async (options) => {
    const globalState = await arc72GetState(options);
    console.log({ globalState });
    return globalState;
});
arc72
    .command("totalSupply")
    .description("Get the total supply of the arc72 token")
    .requiredOption("-a, --apid <number>", "Specify the application ID")
    .action(async (options) => {
    const ci = new CONTRACT(Number(options.apid), algodClient, indexerClient, makeSpec(OSARC72TokenSpec.contract.methods), {
        addr: addr,
        sk: sk,
    });
    const arc72_totalSupplyR = await ci.arc72_totalSupply();
    if (arc72_totalSupplyR.success) {
        console.log(arc72_totalSupplyR.returnValue.toString());
    }
});
arc72
    .command("balanceOf")
    .description("Get the balance of the arc72 token")
    .requiredOption("-a, --apid <number>", "Specify the application ID")
    .requiredOption("-t, --address <string>", "Specify the address")
    .action(async (options) => {
    const ci = new CONTRACT(Number(options.apid), algodClient, indexerClient, makeSpec(OSARC72TokenSpec.contract.methods), {
        addr: addr,
        sk: sk,
    });
    const arc72_balanceOfR = await ci.arc72_balanceOf(options.address);
    if (arc72_balanceOfR.success) {
        console.log(arc72_balanceOfR.returnValue.toString());
    }
});
arc72
    .command("ownerOf")
    .description("Get the owner of the arc72 token")
    .requiredOption("-a, --apid <number>", "Specify the application ID")
    .requiredOption("-t, --token-id <number>", "Specify the token ID")
    .option("-d, --debug", "Debug the deployment", false)
    .action(async (options) => {
    if (options.debug) {
        console.log(options);
    }
    const ci = new CONTRACT(Number(options.apid), algodClient, indexerClient, makeSpec(OSARC72TokenSpec.contract.methods), {
        addr: addr,
        sk: sk,
    });
    const arc72_ownerOfR = await ci.arc72_ownerOf(BigInt(options.tokenId));
    if (arc72_ownerOfR.success) {
        console.log(arc72_ownerOfR.returnValue);
    }
});
arc72
    .command("tokenURI")
    .description("Get the token URI of the arc72 token")
    .requiredOption("-a, --apid <number>", "Specify the application ID")
    .requiredOption("-t, --token-id <number>", "Specify the token ID")
    .action(async (options) => {
    const ci = new CONTRACT(Number(options.apid), algodClient, indexerClient, makeSpec(OSARC72TokenSpec.contract.methods), {
        addr: addr,
        sk: sk,
    });
    const arc72_tokenURIR = await ci.arc72_tokenURI(BigInt(options.tokenId));
    console.log(arc72_tokenURIR);
});
arc72
    .command("mint")
    .description("Mint arc72 token")
    .requiredOption("-a, --apid <number>", "Specify the application ID")
    .requiredOption("-t, --to <string>", "Specify the receiver address")
    .requiredOption("-i, --token-id <number>", "Specify the token ID")
    .option("-m, --metadata <string>", "Specify the metadata")
    .option("-r, --transfer-ownership", "Transfer ownership", false)
    .option("-s, --simulate", "Simulate the mint", false)
    .option("--debug", "Debug the deployment", false)
    .action(async (options) => {
    if (options.debug) {
        console.log(options);
    }
    const apid = Number(options.apid);
    const to = options.to;
    const tokenId = BigInt(options.tokenId);
    const metadata = options.metadata ? new Uint8Array(Buffer.from(padStringWithZeroBytes(options.metadata, 256), "utf8")) : new Uint8Array(256);
    const ci = new CONTRACT(apid, algodClient, indexerClient, abi.custom, {
        addr: addr,
        sk: sk,
    });
    const builder = {
        arc72: new CONTRACT(apid, algodClient, indexerClient, makeSpec(OSARC72TokenSpec.contract.methods), {
            addr: addr,
            sk: sk,
        }, true, false, true),
        ownable: new CONTRACT(Number(options.tokenId), algodClient, indexerClient, makeSpec(OwnableSpec.contract.methods), {
            addr: addr,
            sk: sk,
        }, true, false, true),
    };
    const buildN = [];
    if (options.transferOwnership) {
        const txnO = (await builder.ownable.transfer(algosdk.getApplicationAddress(apid))).obj;
        console.log({ transfer: txnO });
        buildN.push({
            ...txnO,
        });
    }
    const txnO = options.metadata
        ? (await builder.arc72.mint(to, tokenId, metadata)).obj
        : (await builder.arc72.mint(to, tokenId)).obj;
    console.log({ mint: txnO });
    buildN.push({
        ...txnO,
        payment: 336700,
    });
    ci.setFee(3000);
    ci.setEnableGroupResourceSharing(true);
    ci.setExtraTxns(buildN);
    const customR = await ci.custom();
    if (options.debug) {
        console.log(customR);
    }
    if (customR.success) {
        if (!options.simulate) {
            await signSendAndConfirm(customR.txns, sk);
        }
    }
});
arc72
    .command("burn")
    .description("Burn arc72 token")
    .requiredOption("-a, --apid <number>", "Specify the application ID")
    .requiredOption("-t, --token-id <number>", "Specify the token ID")
    .option("-s, --simulate", "Simulate the burn", false)
    .option("--debug", "Debug the deployment", false)
    .action(async (options) => {
    const ci = new CONTRACT(Number(options.apid), algodClient, indexerClient, makeSpec(OSARC72TokenSpec.contract.methods), {
        addr: addr,
        sk: sk,
    });
    ci.setFee(3000);
    const burnR = await ci.burn(BigInt(options.tokenId));
    if (options.debug) {
        console.log(burnR);
    }
    if (burnR.success) {
        if (!options.simulate) {
            await signSendAndConfirm(burnR.txns, sk);
        }
    }
});
arc72
    .command("update")
    .description("Update the arc72 token")
    .requiredOption("-a, --apid <number>", "Specify the application ID")
    .option("-s, --simulate", "Simulate the update", false)
    .option("--debug", "Debug the deployment", false)
    .action(async (options) => {
    const apid = Number(options.apid);
    const res = await new OSARC72TokenClient({
        resolveBy: "id",
        id: apid,
        sender: {
            addr,
            sk,
        },
    }, algodClient).appClient.update();
});
// TODO add post update
arc72
    .command("post-update")
    .description("Post update the arc72 token")
    .requiredOption("-a, --apid <number>", "Specify the application ID")
    .option("-s, --simulate", "Simulate the post update", false)
    .option("--debug", "Debug the deployment", false)
    .action(async (options) => {
    const ci = new CONTRACT(Number(options.apid), algodClient, indexerClient, makeSpec(OSARC72TokenSpec.contract.methods), {
        addr: addr,
        sk: sk,
    });
    const postUpdateR = await ci.post_update();
    if (options.debug) {
        console.log(postUpdateR);
    }
    if (postUpdateR.success) {
        if (!options.simulate) {
            await signSendAndConfirm(postUpdateR.txns, sk);
        }
    }
});
export const arc72Kill = async (options) => {
    const ci = new CONTRACT(Number(options.apid), algodClient, indexerClient, makeSpec(OSARC200TokenSpec.contract.methods), {
        addr: addr,
        sk: sk,
    });
    ci.setPaymentAmount(1e6);
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
arc72
    .command("kill")
    .description("Kill the arc200 token")
    .requiredOption("-a, --apid <number>", "Specify the application ID")
    .option("-s, --simulate", "Simulate the kill", false)
    .option("--debug", "Debug the deployment", false)
    .action(async (options) => {
    const success = await arc72Kill(options);
    console.log("Kill success:", success);
});
// ----------------------------
function numberToByteArray(number, byteLength = 1) {
    if (number < 0 || number >= Math.pow(256, byteLength)) {
        throw new RangeError(`Number ${number} cannot be represented in ${byteLength} bytes.`);
    }
    const byteArray = new Uint8Array(byteLength);
    for (let i = byteLength - 1; i >= 0; i--) {
        byteArray[i] = number & 0xff;
        number = number >> 8;
    }
    return byteArray;
}
const arc72Generate = new Command("generate").description("ARC72 generate utility");
arc72Generate
    .command("generate-royalty-b64")
    .description("Generate royalty b64")
    .requiredOption("-r, --royalty-points <number>", "Specify the royalty points")
    .requiredOption("-c --creator1-points <number>", "Specify the creator1 points")
    .requiredOption("-d --creator2-points <number>", "Specify the creator2 points")
    .requiredOption("-e --creator3-points <number>", "Specify the creator3 points")
    .requiredOption("-f --creator1-address <number>", "Specify the creator1 address")
    .requiredOption("-g --creator2-address <number>", "Specify the creator2 address")
    .requiredOption("-h --creator3-address <number>", "Specify the creator3 address")
    .action(async (options) => {
    const royaltyPoints = Number(options.royaltyPoints);
    const royaltyPointsBytes = numberToByteArray(royaltyPoints, 2);
    const creator1Points = Number(options.creator1Points);
    const creator1PointsBytes = numberToByteArray(creator1Points, 2);
    const creator2Points = Number(options.creator2Points);
    const creator2PointsBytes = numberToByteArray(creator2Points, 2);
    const creator3Points = Number(options.creator3Points);
    const creator3PointsBytes = numberToByteArray(creator3Points, 2);
    const creator1Address = options.creator1Address;
    const creator2Address = options.creator2Address;
    const creator3Address = options.creator3Address;
    const royalty = [
        ...royaltyPointsBytes,
        ...creator1PointsBytes,
        ...creator2PointsBytes,
        ...creator3PointsBytes,
        ...new Uint8Array(algosdk.decodeAddress(creator1Address).publicKey),
        ...new Uint8Array(algosdk.decodeAddress(creator2Address).publicKey),
        ...new Uint8Array(algosdk.decodeAddress(creator3Address).publicKey),
    ];
    console.log(Buffer.from(royalty).toString("base64"));
});
arc72.addCommand(arc72Generate);
// const arc200 = new Command("arc200").description("Manage arc200 token");
// interface ARC200GlobalStateOptions {
//   apid: number;
//   lazy?: boolean;
// }
// export const arc200GetState: any = async (
//   options: ARC200GlobalStateOptions
// ) => {
//   const globalState = await new OSARC200TokenClient(
//     { resolveBy: "id", id: Number(options.apid) },
//     algodClient
//   ).getGlobalState();
//   if (options.lazy) {
//     return { globalState };
//   }
//   const state = {
//     contractVersion: globalState.contractVersion?.asNumber(),
//     deploymentVersion: globalState.deploymentVersion?.asNumber(),
//     owner: algosdk.encodeAddress(
//       globalState.owner?.asByteArray() || new Uint8Array()
//     ),
//     updatable: globalState.updatable?.asNumber(),
//     upgrader: algosdk.encodeAddress(
//       globalState.upgrader?.asByteArray() || new Uint8Array()
//     ),
//     name: stripTrailingZeroBytes(globalState.name?.asString() || ""),
//     symbol: stripTrailingZeroBytes(globalState.symbol?.asString() || ""),
//     totalSupply: uint8ArrayToBigInt(
//       globalState.totalSupply?.asByteArray() || new Uint8Array()
//     ).toString(),
//     decimals: globalState.decimals?.asNumber(),
//   };
//   return state;
// };
// arc200
//   .command("get")
//   .description("Get the state of the arc200 token")
//   .requiredOption("-a, --apid <number>", "Specify the application ID")
//   .action(async (options: ARC200GlobalStateOptions) => {
//     const globalState = await arc200GetState(options);
//     console.log({ globalState });
//     return globalState;
//   });
// interface ARC200MintOptions {
//   apid: number;
//   name: string;
//   symbol: string;
//   totalSupply: number;
//   decimals: number;
//   sender?: string;
//   sk?: any;
//   simulate?: boolean;
//   debug?: boolean;
// }
// export const arc200Mint: any = async (options: ARC200MintOptions) => {
//   const globalState = await new OSARC200TokenClient(
//     { resolveBy: "id", id: Number(options.apid) },
//     algodClient
//   ).getGlobalState();
//   if (options.debug) {
//     console.log(options);
//   }
//   const ci = new CONTRACT(
//     Number(options.apid),
//     algodClient,
//     indexerClient,
//     makeSpec(OSARC200TokenSpec.contract.methods),
//     {
//       addr: options.sender || addr,
//       sk: options.sk || sk,
//     }
//   );
//   ci.setFee(2000);
//   ci.setPaymentAmount(1e6);
//   const mintR = await ci.mint(
//     options.name,
//     options.symbol,
//     options.decimals,
//     options.totalSupply
//   );
//   if (options.debug) {
//     console.log(mintR);
//   }
//   if (mintR.success) {
//     if (!options.simulate) {
//       await signSendAndConfirm(mintR.txns, options.sk || sk);
//     }
//     return true;
//   }
//   return false;
// };
// arc200
//   .command("mint")
//   .description("Get the state of the arc200 token")
//   .requiredOption("-a, --apid <number>", "Specify the application ID")
//   .requiredOption("-n, --name <string>", "Specify the name")
//   .requiredOption("-s, --symbol <string>", "Specify the symbol")
//   .requiredOption("-t, --total-supply <number>", "Specify the total supply")
//   .requiredOption("-d, --decimals <number>", "Specify the decimals")
//   .option("-r, --simulate", "Simulate the mint", false)
//   .option("--debug", "Debug the deployment", false)
//   .action(async (options) => {
//     const success = await arc200Mint({
//       ...options,
//       name: new Uint8Array(
//         Buffer.from(padStringWithZeroBytes(options.name, 32), "utf8")
//       ),
//       symbol: new Uint8Array(
//         Buffer.from(padStringWithZeroBytes(options.symbol, 8), "utf8")
//       ),
//       decimals: Number(options.decimals),
//       totalSupply: BigInt(
//         new BigNumber(options.totalSupply)
//           .multipliedBy(10 ** options.decimals)
//           .toFixed(0)
//       ),
//     });
//     console.log("Mint success:", success);
//   });
// interface ARC200BalanceOfOptions {
//   apid: number;
//   owner: string;
// }
// export const arc200BalanceOf: any = async (options: ARC200BalanceOfOptions) => {
//   const owner = options.owner || addr;
//   const ci = new CONTRACT(
//     Number(options.apid),
//     algodClient,
//     indexerClient,
//     makeSpec(OSARC200TokenSpec.contract.methods),
//     {
//       addr: owner,
//       sk: new Uint8Array(0),
//     }
//   );
//   const balanceR = (await ci.arc200_balanceOf(owner)).returnValue;
//   return balanceR.toString();
// };
// arc200
//   .command("balance")
//   .description("Get the balance of the arc200 token")
//   .requiredOption("-a, --apid <number>", "Specify the application ID")
//   .option("-o, --owner <string>", "Specify the owner address")
//   .action(async (options) => {
//     const balance = await arc200BalanceOf(options);
//     console.log(balance);
//   });
// interface ARC200AllowanceOptions {
//   apid: number;
//   owner: string;
//   spender: string;
// }
// export const arc200Allowance: any = async (options: ARC200AllowanceOptions) => {
//   const owner = options.owner || addr;
//   const spender = options.spender || addr;
//   const ci = new CONTRACT(
//     Number(options.apid),
//     algodClient,
//     indexerClient,
//     makeSpec(OSARC200TokenSpec.contract.methods),
//     {
//       addr: owner,
//       sk: new Uint8Array(0),
//     }
//   );
//   const allowanceR = await ci.arc200_allowance(owner, spender);
//   return allowanceR;
// };
// arc200
//   .command("allowance")
//   .description("Get the allowance of the arc200 token")
//   .requiredOption("-a, --apid <number>", "Specify the application ID")
//   .option("-o, --owner <string>", "Specify the owner address")
//   .option("-s, --spender <string>", "Specify the spender address")
//   .action(async (options) => {
//     const allowance = (await arc200Allowance(options)).returnValue.toString();
//     console.log(allowance);
//   });
// interface ARC200ApproveOptions {
//   apid: number;
//   spender: string;
//   amount: number;
//   simulate?: boolean;
//   debug?: boolean;
// }
// export const arc200Approve: any = async (options: ARC200ApproveOptions) => {
//   const ci = new CONTRACT(
//     Number(options.apid),
//     algodClient,
//     indexerClient,
//     makeSpec(OSARC200TokenSpec.contract.methods),
//     {
//       addr: addr,
//       sk: sk,
//     }
//   );
//   ci.setPaymentAmount(28500 + 3500);
//   const approveR = await ci.arc200_approve(options.spender, options.amount);
//   if (options.debug) {
//     console.log(approveR);
//   }
//   if (approveR.success) {
//     if (!options.simulate) {
//       await signSendAndConfirm(approveR.txns, sk);
//     }
//     return true;
//   }
//   return false;
// };
// arc200
//   .command("approve")
//   .description("Approve the arc200 token")
//   .requiredOption("-a, --apid <number>", "Specify the application ID")
//   .requiredOption("-s, --spender <string>", "Specify the spender address")
//   .requiredOption("-m, --amount <number>", "Specify the amount")
//   .option("-t, --simulate", "Simulate the approval", false)
//   .option("--debug", "Debug the deployment", false)
//   .action(async (options) => {
//     const success = await arc200Approve({
//       ...options,
//       amount: BigInt(options.amount),
//     });
//     console.log("Approve success:", success);
//   });
// interface ARC200TransferOptions {
//   apid: number;
//   receiver: string;
//   amount: number;
//   simulate?: boolean;
//   debug?: boolean;
// }
// export const arc200Transfer: any = async (options: ARC200TransferOptions) => {
//   const ci = new CONTRACT(
//     Number(options.apid),
//     algodClient,
//     indexerClient,
//     makeSpec(OSARC200TokenSpec.contract.methods),
//     {
//       addr: addr,
//       sk: sk,
//     }
//   );
//   ci.setPaymentAmount(28500);
//   const transferR = await ci.arc200_transfer(options.receiver, options.amount);
//   if (options.debug) {
//     console.log(transferR);
//   }
//   if (transferR.success) {
//     if (!options.simulate) {
//       await signSendAndConfirm(transferR.txns, sk);
//     }
//     return true;
//   }
//   return false;
// };
// arc200
//   .command("transfer")
//   .description("Transfer the arc200 token")
//   .requiredOption("-a, --apid <number>", "Specify the application ID")
//   .requiredOption("-r, --receiver <string>", "Specify the receiver address")
//   .requiredOption("-m, --amount <number>", "Specify the amount")
//   .option("-s, --simulate", "Simulate the transfer", false)
//   .option("--debug", "Debug the deployment", false)
//   .action(async (options) => {
//     const success = await arc200Transfer({
//       ...options,
//       amount: BigInt(options.amount),
//     });
//     console.log("Transfer success:", success);
//   });
// arc200
//   .command("update")
//   .description("Update the arc200 token")
//   .requiredOption("-a, --apid <number>", "Specify the application ID")
//   .option("-s, --simulate", "Simulate the update", false)
//   .option("--debug", "Debug the deployment", false)
//   .action(async (options) => {
//     const apid = Number(options.apid);
//     const res = await new OSARC200TokenClient(
//       {
//         resolveBy: "id",
//         id: apid,
//         sender: {
//           addr,
//           sk,
//         },
//       },
//       algodClient
//     ).appClient.update();
//   });
// interface ARC200KillOptions {
//   apid: number;
//   simulate?: boolean;
//   debug?: boolean;
// }
// export const arc200Kill: any = async (options: ARC200KillOptions) => {
//   const ci = new CONTRACT(
//     Number(options.apid),
//     algodClient,
//     indexerClient,
//     makeSpec(OSARC200TokenSpec.contract.methods),
//     {
//       addr: addr,
//       sk: sk,
//     }
//   );
//   ci.setFee(3000);
//   ci.setOnComplete(5); // deleteApplicationOC
//   const killR = await ci.kill();
//   if (options.debug) {
//     console.log(killR);
//   }
//   if (killR.success) {
//     if (!options.simulate) {
//       await signSendAndConfirm(killR.txns, sk);
//     }
//     return true;
//   }
//   return false;
// };
// arc200
//   .command("kill")
//   .description("Kill the arc200 token")
//   .requiredOption("-a, --apid <number>", "Specify the application ID")
//   .option("-s, --simulate", "Simulate the kill", false)
//   .option("--debug", "Debug the deployment", false)
//   .action(async (options) => {
//     const success = await arc200Kill(options);
//     console.log("Kill success:", success);
//   });
// interface AirdropApproveUpdateOptions {
//   apid: number;
//   approval: boolean;
//   simulate?: boolean;
//   sender?: string;
// }
// export const airdropApproveUpdate: any = async (
//   options: AirdropApproveUpdateOptions
// ) => {
//   const ci = makeCi(options.apid, options.sender || addr2);
//   const approveR = await ci.approve_update(options.approval);
//   if (approveR.success) {
//     if (!options.simulate) {
//       await signSendAndConfirm(approveR.txns, sk2);
//     }
//     return true;
//   }
//   return false;
// };
// interface AirdropTransferOptions {
//   apid: number;
//   receiver: number;
//   sender?: string;
//   sk?: any;
//   simulate?: boolean;
//   debug?: boolean;
// }
// export const airdropTransfer: any = async (options: AirdropTransferOptions) => {
//   if (options.debug) {
//     console.log(options);
//   }
//   const ci = makeCi(options.apid, options.sender || addr2);
//   const transferR = await ci.transfer(options.receiver || addr);
//   if (options.debug) {
//     console.log(transferR);
//   }
//   if (transferR.success) {
//     if (!options.simulate) {
//       await signSendAndConfirm(transferR.txns, options.sk || sk2);
//     }
//     return true;
//   }
//   return false;
// };
// interface AirdropSetDelegateOptions {
//   apid: number;
//   delegate: string;
//   simulate?: boolean;
//   sender?: string;
// }
// export const airdropSetDelegate = async (
//   options: AirdropSetDelegateOptions
// ) => {
//   const ci = makeCi(options.apid, options.sender || addr2);
//   const setDelegateR = await ci.set_delegate(options.delegate || addr);
//   if (setDelegateR.success) {
//     if (!options.simulate) {
//       await signSendAndConfirm(setDelegateR.txns, sk2);
//     }
//     return true;
//   }
//   return false;
// };
// interface AirdropSetVersionOptions {
//   apid: number;
//   contractVersion: number;
//   deploymentVersion: number;
//   sender?: string;
//   simulate?: boolean;
//   debug?: boolean;
// }
// export const airdropSetVersion = async (options: AirdropSetVersionOptions) => {
//   const ci = makeCi(options.apid, options?.sender || addr);
//   const setVersionR = await ci.set_version(
//     options.contractVersion,
//     options.deploymentVersion
//   );
//   if (options.debug) {
//     console.log(options);
//     console.log(setVersionR);
//   }
//   if (setVersionR.success) {
//     if (!options.simulate) {
//       await signSendAndConfirm(setVersionR.txns, sk);
//     }
//     return true;
//   }
//   return false;
// };
// interface AirdropGetStateOptions {
//   apid: number;
//   name?: string;
//   lazy?: boolean;
// }
// export const airdropGetState: any = async (options: AirdropGetStateOptions) => {
//   const globalState = await new AirdropClient(
//     { resolveBy: "id", id: Number(options.apid) },
//     algodClient
//   ).getGlobalState();
//   if (options.lazy) {
//     return { globalState };
//   }
//   const state = {
//     contractVersion: globalState.contractVersion?.asNumber(),
//     deadline: globalState.deadline?.asNumber(),
//     delegate: algosdk.encodeAddress(
//       globalState.delegate?.asByteArray() || new Uint8Array()
//     ),
//     deployer: algosdk.encodeAddress(
//       globalState.deployer?.asByteArray() || new Uint8Array()
//     ),
//     deploymentVersion: globalState.deploymentVersion?.asNumber(),
//     distributionCount: globalState.distributionCount?.asNumber(),
//     distributionSeconds: globalState.distributionSeconds?.asNumber(),
//     funder: algosdk.encodeAddress(
//       globalState.funder?.asByteArray() || new Uint8Array()
//     ),
//     funding: globalState.funding?.asNumber(),
//     initial: globalState.initial?.asBigInt().toString(),
//     lockupDelay: globalState.lockupDelay?.asNumber(),
//     messengerId: globalState.messengerId?.asNumber(),
//     owner: algosdk.encodeAddress(
//       globalState.owner?.asByteArray() || new Uint8Array()
//     ),
//     parentId: globalState.parentId?.asNumber(),
//     period: globalState.period?.asNumber(),
//     periodLimit: globalState.periodLimit?.asNumber(),
//     periodSeconds: globalState.periodSeconds?.asNumber(),
//     stakeable: globalState.stakeable?.asNumber(),
//     total: globalState.total?.asBigInt().toString(),
//     updatable: globalState.updatable?.asNumber(),
//     upgrader: algosdk.encodeAddress(
//       globalState.upgrader?.asByteArray() || new Uint8Array()
//     ),
//     vestingDelay: globalState.vestingDelay?.asNumber(),
//   };
//   return state;
// };
// airdrop
//   .command("get")
//   .description("Get the state of the airdrop contract")
//   .requiredOption("-a, --apid <number>", "Specify the application ID")
//   .action(airdropGetState);
// airdrop
//   .command("list")
//   .description("List all airdrop contracts")
//   .action(async () => {
//     const {
//       data: { accounts },
//     } = await axios.get(
//       `${arc72IndexerURL}/v1/scs/accounts?parentId=${CTC_INFO_FACTORY_AIRDROP}&deleted=0`
//     );
//     for await (const account of accounts) {
//       console.log(account);
//     }
//   });
// interface AirdropReduceTotalOptions {
//   apid: number;
//   amount: number;
//   simulate?: boolean;
//   sender?: string;
// }
// export const airdropReduceTotal: any = async (
//   options: AirdropReduceTotalOptions
// ) => {
//   const ci = makeCi(Number(options.apid), options.sender || addr);
//   const reduceR = await ci.reduce_total(Number(options.amount) * 1e6);
//   if (reduceR.success) {
//     await signSendAndConfirm(reduceR.txns, sk);
//     return true;
//   }
//   return false;
// };
// airdrop
//   .command("reduce-total <amount>")
//   .requiredOption("-a, --amount <number>", "Specify the amount to reduce")
//   .action(airdropReduceTotal);
// interface AirdropAbortFundingOptions {
//   apid: number;
//   simulate?: boolean;
//   sender?: string;
//   debug?: boolean;
// }
// export const airdropAbortFunding: any = async (
//   options: AirdropAbortFundingOptions
// ) => {
//   const ci = makeCi(Number(options.apid), options.sender || addr);
//   ci.setFee(3000);
//   ci.setOnComplete(5); // deleteApplicationOC
//   const abortR = await ci.abort_funding();
//   if (options.debug) {
//     console.log(options);
//     console.log(abortR);
//   }
//   if (abortR.success) {
//     if (!options.simulate) {
//       await signSendAndConfirm(abortR.txns, sk);
//     }
//     return true;
//   }
//   return false;
// };
// airdrop
//   .command("abort-funding")
//   .description("Abort funding for the airdrop")
//   .option("-a, --apid <number>", "Specify the application ID")
//   .action(airdropAbortFunding);
// airdrop
//   .command("setup <ownerAddr>")
//   .description("Setup owner and funder for the contract")
//   .action(async (ownerAddr) => {
//     const ci = makeCi(Number(CTC_INFO_AIRDROP), addr);
//     ci.setPaymentAmount(0.1 * 1e6);
//     const setupR = await ci.setup(ownerAddr, addr);
//     console.log(setupR);
//     const res = await signSendAndConfirm(setupR.txns, sk);
//     console.log(res);
//   });
// // configure the airdrop contract as default owner addr2
// interface AirdropConfigureOptions {
//   apid: number;
//   period: number;
//   sender?: string;
//   sk?: any;
//   simulate?: boolean;
//   debug?: boolean;
// }
// export const airdropConfigure: any = async (
//   options: AirdropConfigureOptions
// ) => {
//   if (options.debug) {
//     console.log(options);
//   }
//   const ctcInfo = Number(options.apid);
//   const period = Number(options.period || 0);
//   const ci = makeCi(ctcInfo, options.sender || addr2);
//   const configureR = await ci.configure(period);
//   if (options.debug) {
//     console.log(configureR);
//   }
//   if (configureR.success) {
//     if (!options.simulate) {
//       await signSendAndConfirm(configureR.txns, options.sk || sk2);
//     }
//     return true;
//   }
//   return false;
// };
// airdrop
//   .command("configure")
//   .description("Configure the lockup period")
//   .requiredOption("-a, --apid <number>", "Specify the application ID")
//   .option("-p, --period <number>", "Specify the lockup period")
//   .option("--debug", "Debug the deployment", false)
//   .action(airdropConfigure);
// interface AirdropFillOptions {
//   apid: number;
//   amount: number;
//   simulate?: boolean;
//   timestamp?: number;
//   sender?: string;
//   sk?: any;
//   debug?: boolean;
// }
// export const airdropFill: any = async (options: AirdropFillOptions) => {
//   if (options.debug) {
//     console.log(options);
//   }
//   const timestamp = Number(options.timestamp || 0);
//   if (timestamp <= 0) {
//     const ci = makeCi(Number(options.apid), options.sender || addr);
//     const paymentAmount = Number(options.amount) * 1e6;
//     ci.setPaymentAmount(paymentAmount);
//     const fillR = await ci.fill();
//     if (options.debug) {
//       console.log(fillR);
//     }
//     if (fillR.success) {
//       if (!options.simulate) {
//         await signSendAndConfirm(fillR.txns, options.sk || sk);
//       }
//       return true;
//     }
//     return false;
//   } else {
//     const ci = new CONTRACT(
//       Number(options.apid),
//       algodClient,
//       indexerClient,
//       abi.custom,
//       {
//         addr,
//         sk: new Uint8Array(0),
//       }
//     );
//     const builder = new CONTRACT(
//       Number(options.apid),
//       algodClient,
//       indexerClient,
//       makeSpec(AirdropSpec.contract.methods),
//       {
//         addr,
//         sk: new Uint8Array(0),
//       },
//       true,
//       false,
//       true
//     );
//     const buildN = [];
//     buildN.push({
//       ...(await builder.fill()).obj,
//       payment: Number(options.amount) * 1e6,
//     });
//     buildN.push({
//       ...(await builder.set_funding(timestamp)).obj,
//     });
//     ci.setFee(1000);
//     ci.setEnableGroupResourceSharing(true);
//     ci.setExtraTxns(buildN);
//     const customR = await ci.custom();
//     if (options.debug) {
//       console.log(customR);
//     }
//     if (customR.success) {
//       if (!options.simulate) {
//         await signSendAndConfirm(customR.txns, sk);
//       }
//       return true;
//     }
//     return false;
//   }
// };
// airdrop
//   .command("fill")
//   .description("Fill the staking contract")
//   .requiredOption("-a, --apid <number>", "Specify the application ID")
//   .requiredOption("-f, --amount <number>", "Specify the amount to fill")
//   .option("-s, --simulate", "Simulate the fill", false)
//   .option("-g --timestamp <number>", "Funding timestamp")
//   .option("--debug", "Debug the deployment", false)
//   .action(airdropFill);
// interface AirdropSetFundingOptions {
//   apid: number;
//   timestamp: number;
//   simulate?: boolean;
//   debug?: boolean;
// }
// export const airdropSetFunding: any = async (
//   options: AirdropSetFundingOptions
// ) => {
//   if (options.debug) {
//     console.log(options);
//   }
//   const ctcInfo = Number(options.apid);
//   const timestamp = Number(options.timestamp || 0);
//   const ci = makeCi(ctcInfo, addr);
//   const set_fundingR = await ci.set_funding(timestamp);
//   if (options.debug) {
//     console.log(set_fundingR);
//   }
//   if (set_fundingR.success) {
//     if (!options.simulate) {
//       await signSendAndConfirm(set_fundingR.txns, sk);
//     }
//     return true;
//   }
//   return false;
// };
// airdrop
//   .command("set-funding")
//   .description("Set the funding timestamp")
//   .requiredOption("-a, --apid <number>", "Specify the application ID")
//   .requiredOption("-t, --timestamp <number>", "Specify the timestamp")
//   .option("--debug", "Debug the deployment", false)
//   .action(airdropSetFunding);
// interface AirdropParticipateOptions {
//   apid: number;
//   vote_k: Uint8Array[];
//   sel_k: Uint8Array[];
//   vote_fst: number;
//   vote_lst: number;
//   vote_kd: number;
//   sp_key: Uint8Array[];
//   sender?: string;
//   simulate?: boolean;
//   debug?: boolean;
// }
// export const airdropParticipate: any = async (
//   options: AirdropParticipateOptions
// ) => {
//   if (options.debug) {
//     console.log(options);
//   }
//   const ctcInfo = Number(options.apid);
//   const ci = makeCi(ctcInfo, options.sender || addr2);
//   ci.setPaymentAmount(1000);
//   const participateR = await ci.participate(
//     options.vote_k,
//     options.sel_k,
//     options.vote_fst,
//     options.vote_lst,
//     options.vote_kd,
//     options.sp_key
//   );
//   if (options.debug) {
//     console.log(options);
//     console.log(participateR);
//   }
//   if (participateR.success) {
//     if (!options.simulate) {
//       await signSendAndConfirm(participateR.txns, sk2);
//     }
//     return true;
//   }
//   return false;
// };
// airdrop
//   .command("participate")
//   .description("Participate in the airdrop")
//   .option("-a, --apid <number>", "Specify the application ID")
//   .option("-k, --vote-k <string>", "Specify the vote key")
//   .option("-s, --sel-k <string>", "Specify the selection key")
//   .option("-f, --vote-fst <number>", "Specify the vote first")
//   .option("-l, --vote-lst <number>", "Specify the vote last")
//   .option("-d, --vote-kd <number>", "Specify the vote key duration")
//   .action(airdropParticipate);
// interface AirdropDepositOptions {
//   apid: number;
//   amount: number;
//   address?: string;
// }
// export const airdropDeposit = async (options: AirdropDepositOptions) => {
//   const txn = algosdk.makePaymentTxnWithSuggestedParamsFromObject({
//     from: options.address || addr2,
//     to: algosdk.getApplicationAddress(options.apid),
//     amount: Number(options.amount) * 1e6,
//     suggestedParams: await algodClient.getTransactionParams().do(),
//   });
//   const signedTxn = txn.signTxn(sk2);
//   const { txId } = await algodClient.sendRawTransaction(signedTxn).do();
//   const result = await waitForConfirmation(algodClient, txId, 3);
//   return !result["pool-error"];
// };
// interface AirdropWithdrawOptions {
//   apid: number;
//   amount: number;
//   sender?: string;
//   simulate?: boolean;
//   debug?: boolean;
// }
// export const airdropWithdraw: any = async (options: AirdropWithdrawOptions) => {
//   const ci = makeCi(Number(options.apid), options.sender || addr2);
//   const withdrawAmount = Number(options.amount) * 1e6;
//   ci.setFee(2000);
//   const withdrawR = await ci.withdraw(withdrawAmount);
//   if (options.debug) {
//     console.log(options);
//     console.log(withdrawR);
//   }
//   if (withdrawR.success) {
//     if (!options.simulate) {
//       await signSendAndConfirm(withdrawR.txns, sk2);
//     }
//     return true;
//   } else {
//     return false;
//   }
// };
// interface AirdropGetMbOptions {
//   apid: number;
//   address: string;
//   debug?: boolean;
// }
// export const airdropGetMb: any = async (options: AirdropGetMbOptions) => {
//   if (options.debug) {
//     console.log(options);
//   }
//   const ctcInfo = Number(options.apid);
//   const ci = makeCi(ctcInfo, options.address || addr2);
//   ci.setFee(2000);
//   const withdrawR = await ci.withdraw(0);
//   if (options.debug) {
//     console.log(withdrawR);
//   }
//   if (withdrawR.success) {
//     const withdraw = withdrawR.returnValue;
//     return withdraw.toString();
//   } else {
//     return "0";
//   }
// };
// airdrop
//   .command("get-mb")
//   .description("Simulate owner's withdrawal and log 'mab' value")
//   .option("-a, --apid <number>", "Specify the application ID")
//   .option("-d, --address <string>", "Specify the address")
//   .option("--debug", "Debug the deployment", false)
//   .action(async (options: AirdropGetMbOptions) => {
//     const mab = await airdropGetMb(options);
//     console.log(mab);
//   });
// interface AirdropCloseOptions {
//   apid: number;
//   simulate?: boolean;
//   sender?: string;
//   debug?: boolean;
// }
// export const airdropClose: any = async (options: AirdropCloseOptions) => {
//   if (options.debug) {
//     console.log(options);
//   }
//   const ctcInfo = Number(options.apid);
//   const ci = makeCi(ctcInfo, options.sender || addr);
//   ci.setFee(3000);
//   ci.setOnComplete(5); // deleteApplicationOC
//   const closeR = await ci.close();
//   if (options.debug) {
//     console.log(closeR);
//   }
//   if (closeR.success) {
//     if (!options.simulate) {
//       await signSendAndConfirm(closeR.txns, sk);
//     }
//     return true;
//   }
//   return false;
// };
// airdrop
//   .command("close")
//   .description("Close the airdrop contract")
//   .option("-a, --apid <number>", "Specify the application ID")
//   .option("-s, --simulate", "Simulate the close", false)
//   .option("-d --debug", "Debug the close")
//   .option("t --sender <string>", "Specify the sender")
//   .action(airdropClose);
program.addCommand(arc72);
//program.addCommand(arc200);
// program.addCommand(factory);
