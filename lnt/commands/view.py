# Mark standard lib imports
import time, datetime, calendar
from decimal import Decimal

# Mark 3rd party lib imports
import click

# Mark Local imports
from lnt.rpc.api import listChannels, getChanInfo, getForwardingHistory, closedChannels, pendingChannels
from lnt.constants import VIEW_CHANNEL_COLUMNS_DEFAULT, VIEW_CHANNEL_COLUMNS_MAP
from lnt.commands.utils.utils import get_1ml_info


def channel(ctx):

    def print_tables(ctx, testnet):
        # ListChannels RPC call
        channels = listChannels(ctx, active_only=False)

        num_channels_with_peer = {}

        fwd_hist_start_time = calendar.timegm((datetime.date.today() - \
            datetime.timedelta(ctx.monthsago*365/12)).timetuple())

        fwd_hist_end_time = calendar.timegm(datetime.date.today().timetuple())

        # ForwardingHistory RPC call
        for fwd_event in getForwardingHistory(ctx, fwd_hist_start_time, fwd_hist_end_time):
            try:
                channels[str(fwd_event.chan_id_in)]['forward_incoming'] += 1
            except KeyError:
                pass
            try:
                channels[str(fwd_event.chan_id_out)]['forward_outgoing'] += 1
            except KeyError:
                pass

        # Per channel chores
        for ch_id in list(channels):
            chan_info = getChanInfo(ctx, chan_id=int(ch_id))
            ml_info = get_1ml_info(testnet, channels[ch_id]['remote_pubkey'])

            # TODO: capacity seems to get weird here
            channels[ch_id] = { **channels[ch_id], **chan_info, **ml_info }


            # Prep for ForwardHistory call
            channels[ch_id]['forward_incoming'] = 0
            channels[ch_id]['forward_outgoing'] = 0
            channels[ch_id]['forwards'] = channels[ch_id]['forward_incoming'] + channels[ch_id]['forward_outgoing']
            channels[ch_id]['local/cap'] = round((Decimal(channels[ch_id]['local_balance'])/ Decimal(channels[ch_id]['capacity']))*100, 2)

            # Count channels by peer
            num_channels_with_peer[channels[ch_id]['remote_pubkey']] = num_channels_with_peer.get(channels[ch_id]['remote_pubkey'], 0) + 1

        # Sort the things
        if ctx.sort:
            sort_key = VIEW_CHANNEL_COLUMNS_MAP[(ctx.max or ctx.min).upper()]
            sorted_channels = sorted(channels.items(), key=lambda kv: kv[1][sort_key])

        if ctx.max:
            sorted_channels.reverse()

        if ctx.csv:
            header = ",".join(VIEW_CHANNEL_COLUMNS_DEFAULT)
        else:
            prnt_str = format_str.format(
                            str(ch_id).ljust(20),
                            str(channel['capacity']).ljust(11),
                            str(channel['local_balance']).ljust(10),
                            str(channel['local/cap']).rjust(8),
                            str(channel['forwards']).ljust(10).rjust(12),
                            str(len(channel['pending_htlcs'])).ljust(15),
                            str(time.strftime('%Y-%m-%d %H:%M', time.gmtime(channel['last_update']))).ljust(18),
                            str(num_channels_with_peer[channel['remote_pubkey']]).ljust(18),
                            str(channel.get('alias', ''))
                            )

        click.echo(prnt_str)
    return