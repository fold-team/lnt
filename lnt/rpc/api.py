# Mark 3rd party lib imports
import click
import lnt.rpc.rpc_pb2 as ln, lnt.rpc.rpc_pb2_grpc as lnrpc

# Mark local imports
from lnt.commands.utils import utils, rebal

def listChannels(ctx, active_only:bool=False):
    request = ln.ListChannelsRequest(active_only=False)
    response = ctx.stub.ListChannels(request, metadata=[('macaroon', ctx.macaroon)])
    channels = utils.normalize_channels(response.channels)

    return channels

def getChanInfo(ctx, chan_id: int):
    request = ln.ChanInfoRequest(chan_id=chan_id)
    response = ctx.stub.GetChanInfo(request, metadata=[('macaroon', ctx.macaroon)])
    chan_info = utils.normalize_get_chan_response(response)

    return chan_info

def getForwardingHistory(ctx, start_time, end_time, num_max_events=10000):
    request = ln.ForwardingHistoryRequest(
        start_time=start_time,
        end_time=end_time,
        num_max_events=num_max_events
    )
    response = ctx.stub.ForwardingHistory(request, metadata=[('macaroon', ctx.macaroon)])

    return tuple(response.forwarding_events)

def closeChannel(ctx, channel_point, streaming:bool, force:bool=False, target_conf:int=None, sat_per_byte:int=None):
    testnet = ctx.parent.parent.config['LNT']['testnet']

    request = ln.CloseChannelRequest(
        channel_point=channel_point,
        force=force,
        target_conf=target_conf,
        sat_per_byte=sat_per_byte,
    )

    for response in ctx.stub.CloseChannel(request, metadata=[('macaroon', ctx.macaroon)]):
        if streaming:
            if response.close_pending:
                tx = response.close_pending.txid[::-1].hex()
                click.echo(
                "Closing Tx Confirming: {}\nView it here: https://blockstream.info{}{}"\
                    .format(tx, '/testnet/' if testnet else '/', tx))
            elif response.chan_close:
                tx = response.chan_close.txid[::-1].hex()
                click.echo(
                "Closing Tx Confirmed: {}\nView it here: https://blockstream.info{}{}"\
                    .format(tx, '/testnet/' if testnet else '/', tx))
                break
        else:
            return response.close_pending.txid[::-1].hex()

def closedChannels(ctx, cooperative:bool=None, local_force:bool=None, remote_force:bool=None, breach:bool=None,
    funding_canceled:bool=None, abandoned:bool=None):

    request = ln.ClosedChannelsRequest(
        cooperative=cooperative,
        local_force=local_force,
        remote_force=remote_force,
        breach=breach,
        funding_canceled=funding_canceled,
        abandoned=abandoned,
    )

    # No normalization required for some reason
    return ctx.stub.ClosedChannels(request, metadata=[('macaroon', ctx.macaroon)])

def pendingChannels(ctx):
    request = ln.PendingChannelsRequest()
    response = ctx.stub.PendingChannels(request, metadata=[('macaroon'), macaroon)])

    # Will probably have to normalize this. If you end up debugging here - that's why
    return response
    
    # { 
    #     "total_limbo_balance": <int64>,
    #     "pending_open_channels": <array PendingOpenChannel>,
    #     "pending_closing_channels": <array ClosedChannel>,
    #     "pending_force_closing_channels": <array ForceClosedChannel>,
    #     "waiting_close_channels": <array WaitingCloseChannel>,
    # }
