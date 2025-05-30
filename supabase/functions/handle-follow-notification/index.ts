import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Create a Supabase client with the Auth context of the logged in user
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
    )

    // Get the Auth payload from the request
    const payload = await req.json()
    const { record } = payload

    if (!record) {
      throw new Error('No record in the payload')
    }

    // Get follower's information
    const { data: followerData, error: followerError } = await supabaseClient
      .from('profiles')
      .select('username')
      .eq('id', record.follower_id)
      .single()

    if (followerError) throw followerError

    // Get push subscriptions for the followed user
    const { data: subscriptions, error: subscriptionError } = await supabaseClient
      .from('push_subscriptions')
      .select('*')
      .eq('user_id', record.following_id)

    if (subscriptionError) throw subscriptionError

    // Send notifications to all subscriptions
    const notifications = subscriptions.map(async (subscription) => {
      const message = {
        message: `${followerData.username} a commencé à vous suivre !`,
        url: `/profile/${followerData.username}`
      }

      const vapidHeaders = {
        typ: 'JWT',
        alg: 'ES256'
      }

      const audience = new URL(subscription.endpoint).origin

      const vapidPayload = {
        aud: audience,
        exp: Math.floor(Date.now() / 1000) + (12 * 60 * 60),
        sub: 'mailto:votre@email.com'  // Remplacez par votre email
      }

      // Encodage du header et payload en base64url
      const encodeBase64URL = (data) => {
        return btoa(JSON.stringify(data))
          .replace(/=+$/, '')
          .replace(/\+/g, '-')
          .replace(/\//g, '_')
      }

      const jwtHeader = encodeBase64URL(vapidHeaders)
      const jwtPayload = encodeBase64URL(vapidPayload)

      const key = await crypto.subtle.importKey(
        'pkcs8',
        Deno.env.get('VAPID_PRIVATE_KEY'),
        {
          name: 'ECDSA',
          namedCurve: 'P-256'
        },
        false,
        ['sign']
      )

      const signature = await crypto.subtle.sign(
        { name: 'ECDSA', hash: 'SHA-256' },
        key,
        new TextEncoder().encode(`${jwtHeader}.${jwtPayload}`)
      )

      const jwt = `${jwtHeader}.${jwtPayload}.${encodeBase64URL(signature)}`

      const response = await fetch(subscription.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `vapid t=${jwt}, k=${Deno.env.get('VAPID_PUBLIC_KEY')}`,
          'Content-Length': JSON.stringify(message).length.toString(),
          'TTL': '86400'
        },
        body: JSON.stringify(message)
      })

      if (!response.ok && response.status === 410) {
        // Subscription has expired or been unsubscribed
        const { error } = await supabaseClient
          .from('push_subscriptions')
          .delete()
          .eq('id', subscription.id)

        if (error) throw error
      }
    })

    await Promise.all(notifications)

    return new Response(
      JSON.stringify({ success: true }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    )

  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400 
      }
    )
  }
})
